from SuperMerchant import SuperMerchant
import os
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.models import Offer
import argparse
import pickle
from utils import download_data_and_aggregate, learn_from_csvs, extract_features_from_offer_snapshot, TrainingData, calculate_performance
from sklearn.linear_model import LogisticRegression
import datetime
import logging
import pandas as pd
import numpy as np
import random


MODELS_FILE = 'log_reg_models.pkl'

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl'
print(merchant_token)

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'kafka_reverse_proxy_url': MerchantBaseLogic.get_kafka_reverse_proxy_url(),
    'debug': True,
    'max_amount_of_offers': 10,
    'shipping': 2,
    'primeShipping': 1,
    'max_req_per_sec': 10.0,
    'learning_interval': 2.0,
}


def load_history():
    with open(MODELS_FILE, 'rb') as m:
        return pickle.load(m)


def save_features(features_per_situation):
    with open(MODELS_FILE, 'wb') as m:
        pickle.dump(features_per_situation, m)


class MLMerchant(SuperMerchant):
    def __init__(self):
        super().__init__(merchant_token, settings)

        td = TrainingData(merchant_token, self.merchant_id)
        td.append_by_csvs('../data/marketSituation.csv', '../data/buyOffer.csv')
        # td.store_as_json()
        td.print_info()
        sales_vector, features_vector = td.create_training_data('1')
        model = LogisticRegression()
        model.fit(features_vector, sales_vector)

        probas = model.predict_proba(features_vector)
        calculate_performance([x[1] for x in probas], sales_vector, 1)
        
        import pdb; pdb.set_trace()
        # td.append_by_kafka()
        # td.print_info()
        td.append_by_kafka('../data/marketSituation_kafka.csv', '../data/buyOffer_kafka.csv')
        td.print_info()

        if os.path.isfile(MODELS_FILE):
            self.machine_learning()
            self.last_learning = datetime.datetime.now()
        else:
            self.initial_learning()
        self.run_logic_loop()

    def initial_learning(self):
        features_per_situation = learn_from_csvs(merchant_token)
        save_features(features_per_situation)
        self.product_models = self.train_model(features_per_situation)
        # TODO kafka learning
        self.last_learning = datetime.datetime.now()

    def machine_learning(self):
        history = load_history()
        features_per_situation = download_data_and_aggregate(merchant_token, self.merchant_id)
        if features_per_situation:
            # TODO does that work ??
            try:
                history.update(features_per_situation)
            except Exception:
                print(features_per_situation)
            save_features(features_per_situation)
            self.product_models = self.train_model(features_per_situation)

    def execute_logic(self):
        next_training_session = self.last_learning \
            + datetime.timedelta(minutes=self.settings['learning_interval'])
        if next_training_session <= datetime.datetime.now():
            self.last_learning = datetime.datetime.now()
            self.machine_learning()

        request_count = 0

        try:
            offers = self.marketplace_api.get_offers(include_empty_offers=False)
        except Exception as e:
            logging.warning('Could not receive offers from marketplace: {}'.format(e))
            raise e

        own_offers = [offer for offer in offers if offer.merchant_id == self.merchant_id]
        own_offers_by_uid = {offer.uid: offer for offer in own_offers}
        missing_offers = settings['max_amount_of_offers'] - sum(offer.amount for offer in own_offers)

        new_products = []
        for _ in range(missing_offers):
            try:
                prod = self.producer_api.buy_product()
                new_products.append(prod)
            except Exception as e:
                logging.warning('Could not buy new product from producer api: {}'.format(e))
                raise e

        try:
            products = self.producer_api.get_products()
            product_prices_by_uid = {product.uid: product.price for product in products}
        except Exception as e:
            logging.warning('Could not buy receive products from producer api: {}'.format(e))

        for own_offer in own_offers:
            if own_offer.amount > 0:
                own_offer.price = self.calculate_optimal_price(own_offer, product_prices_by_uid, current_offers=offers)
                try:
                    self.marketplace_api.update_offer(own_offer)
                    request_count += 1
                except Exception as e:
                    logging.warning('Could not update offer on marketplace: {}'.format(e))

        for product in new_products:
            try:
                if product.uid in own_offers_by_uid:
                    offer = own_offers_by_uid[product.uid]
                    offer.amount += product.amount
                    offer.signature = product.signature
                    try:
                        self.marketplace_api.restock(offer.offer_id, amount=product.amount, signature=product.signature)
                    except Exception as e:
                        print('error on restocking an offer:', e)
                    offer.price = self.calculate_optimal_price(product, product_prices_by_uid, current_offers=offers)
                    try:
                        self.marketplace_api.update_offer(offer)
                        request_count += 1
                    except Exception as e:
                        print('error on updating an offer:', e)
                else:
                    offer = Offer.from_product(product)
                    offer.prime = True
                    offer.shipping_time['standard'] = self.settings['shipping']
                    offer.shipping_time['prime'] = self.settings['primeShipping']
                    offer.merchant_id = self.merchant_id
                    offer.price = self.calculate_optimal_price(product, product_prices_by_uid, current_offers=offers+[offer])
                    try:
                        self.marketplace_api.add_offer(offer)
                    except Exception as e:
                        print('error on adding an offer to the marketplace:', e)
            except Exception as e:
                print('could not handle product:', product, e)

        return max(1.0, request_count) / settings['max_req_per_sec']

    def calculate_optimal_price(self, product, product_prices_by_uid, current_offers=None):
        """
        Computes a price for a product based on trained models or (exponential) random fallback
        :param product: product object that is to be priced
        :param current_offers: list of offers
        :return:
        """

        price = product_prices_by_uid[product.uid]

        if random.uniform(0, 1) < 0.3:
            print("RAND \n\n\n\n\n")
            return (random.randint(price * 100, 10000) / 100)
        try:
            model = self.product_models[str(product.product_id)]

            offer_df = pd.DataFrame([o.to_dict() for o in current_offers])
            offer_df = offer_df[offer_df['product_id'] == product.product_id]
            own_offers_mask = offer_df['merchant_id'] == self.merchant_id

            features = []
            for potential_price in range(1, 100, 1):
                potential_price_candidate = potential_price / 10.0
                potential_price = price + potential_price_candidate #product.price + potential_price_candidate
                offer_df.loc[own_offers_mask, 'price'] = potential_price
                features.append(extract_features_from_offer_snapshot(potential_price, current_offers, self.merchant_id,
                                                                     product.product_id))

                probas = model.predict_proba(features)[:, 1]
                max_expected_profit = 0
                for i, f in enumerate(features):
                    expected_profit = probas[i] * (f[0] - price)
                    if expected_profit > max_expected_profit:
                        max_expected_profit = expected_profit
                        best_price = f[0]
                print(best_price)
                return best_price
        except (KeyError, ValueError):
            # Fallback for new porduct
            print("RANDOMMMMMMMMM")
            return price * (np.random.exponential() + 0.99)

    def train_model(self, features):
        # TODO include time and amount of sold items to featurelist
        logging.debug('Start training')
        model_products = dict()

        for product_id, vector_tuple in features.items():
            model = LogisticRegression()
            model.fit(vector_tuple[0], vector_tuple[1])

            model_products[product_id] = model
        logging.debug('Finished training')
        return model_products

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description='PriceWars Merchant doing fancy ML')
    parser.add_argument('--port',
                        type=int,
                        default=5101,
                        help='Port to bind flask App to, default is 5100')
    args = parser.parse_args()
    server = MerchantServer(MLMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
