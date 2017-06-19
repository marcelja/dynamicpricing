from SuperMerchant import SuperMerchant
import os
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.models import Offer
import argparse
import pickle
from utils import download_data_and_aggregate, learn_from_csvs, extract_features_from_offer_snapshot
from sklearn.linear_model import LogisticRegression
import datetime
import logging
import pandas as pd
import numpy as np


MODELS_FILE = 'models.pkl'

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = 'SRRwm8BPitYRO2oMm0ioSJo9kT3SdEj5eC2RKDr37QUVRIrFJZ4ktstdMw6zBq5p'
    merchant_token = '37HNK9QRYtv1DnFVOJHHCBvY82YJsd9vlQI6ZiW8cT9pHOLehcwtnsTvu2EnfNiR' 
    merchant_token = 'n2WNk4VNWdDn2YSjBPeyH7tC99zoWiFKkmgUpCrMp5Arddco2GmKOhWXpWLMFbgy' 

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
    'learning_interval': 1.0,
}


def load_history():
    # Next line can be removed, when csv learning is implemented
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE, 'rb') as m:
            models = pickle.load(m)
    else:
        models = dict()
    return models


def save_features(features_per_situation):
    # This might not work so far
    with open(MODELS_FILE, 'wb') as m:
        pickle.dump(features_per_situation, m)


class MLMerchant(SuperMerchant):
    def __init__(self):
        super().__init__(merchant_token, settings)
        download_data_and_aggregate(merchant_token, self.merchant_id)
        raise
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
        # TODO does that work
        history.update(features_per_situation)
        save_features(features_per_situation)
        models = self.train_model(features_per_situation)

        return models

    def execute_logic(self):
        next_training_session = self.last_learning \
            + datetime.timedelta(minutes=self.settings['learning_interval'])
        if next_training_session <= datetime.datetime.now():
            self.last_learning = datetime.datetime.now()
            self.product_models = self.machine_learning()

        request_count = 0

        try:
            offers = self.marketplace_api.get_offers(include_empty_offers=True)
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
        print("calc optimal price")

        price = product_prices_by_uid[product.uid]
        try:
            # model = self.model_products[product.product_id]
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
            # data = pd.DataFrame(features).dropna()
            # TODO: could be second row, currently
            try:
                pass
                # filtered = data[['amount_of_all_competitors',
                #                  'average_price_on_market',
                #                  'distance_to_cheapest_competitor',
                #                  'price_rank',
                #                  'quality_rank',
                #                  ]]
                probas = model.predict_proba(features)[:, 1]
                max_expected_profit = 0
                for i, f in enumerate(features):
                    expected_profit = probas[i] * (f[0] - price)
                    if expected_profit > max_expected_profit:
                        max_expected_profit = expected_profit
                        best_price = f[0]
                print(best_price)
                return best_price
            except Exception as e:
                print(e)
        except (KeyError, ValueError) as e:
            # Fallback for new porduct
            print("RANDOMMMMMMMMM")
            return price * (np.random.exponential() + 0.99)
        except Exception as e:
            pass

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
                        default=5100,
                        help='Port to bind flask App to, default is 5100')
    args = parser.parse_args()
    server = MerchantServer(MLMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
