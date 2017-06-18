from SuperMerchant import SuperMerchant
import os
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.models import Offer
import argparse
import pickle
from utils import download_data_and_aggregate, extract_features_from_offer_snapshot
from sklearn.linear_model import LogisticRegression
import datetime
import logging
import pandas as pd
import numpy as np


MODELS_FILE = 'models.pkl'

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = 'XUQfD1aKdJAsEUrqsb2XDpPnm4dotzDRUd7heh2I0CCEg35Ze77rwWfjaJYUJkvn'

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
        self.last_learning = datetime.datetime.now()
        self.product_models = self.machine_learning()
        self.run_logic_loop()

    def machine_learning(self):
        history = load_history()
        features_per_situation = download_data_and_aggregate(merchant_token)

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

    def calculate_optimal_price(self, product_or_offer, product_prices_by_uid, current_offers=None):
        """
        Computes a price for a product based on trained models or (exponential) random fallback
        :param product_or_offer: product object that is to be priced
        :param current_offers: list of offers
        :return:
        """
        price = product_prices_by_uid[product_or_offer.uid]
        try:
            model = self.models_per_product[product_or_offer.product_id]

            offer_df = pd.DataFrame([o.to_dict() for o in current_offers])
            offer_df = offer_df[offer_df['product_id'] == product_or_offer.product_id]
            own_offers_mask = offer_df['merchant_id'] == self.merchant_id

            features = []
            for potential_price in range(1, 100, 1):
                potential_price_candidate = potential_price / 10.0
                potential_price = price + potential_price_candidate #product_or_offer.price + potential_price_candidate
                offer_df.loc[own_offers_mask, 'price'] = potential_price
                features.append(extract_features_from_offer_snapshot(offer_df, self.merchant_id,
                                                                     product_id=product_or_offer.product_id))
            data = pd.DataFrame(features).dropna()
            # TODO: could be second row, currently
            try:
                filtered = data[['amount_of_all_competitors',
                                 'average_price_on_market',
                                 'distance_to_cheapest_competitor',
                                 'price_rank',
                                 'quality_rank',
                                 ]]
                data['sell_prob'] = model.predict_proba(filtered)[:, 1]
                data['expected_profit'] = data['sell_prob'] * (data['own_price'] - price)
                print("set price as ", data['own_price'][data['expected_profit'].argmax()])
            except Exception as e:
                print(e)
            
            return data['own_price'][data['expected_profit'].argmax()]
        except (KeyError, ValueError) as e:
            # Fallback for new porduct
            return price * (np.random.exponential() + 0.99)
        except Exception as e:
            pass

    def train_model(self, features):
        # TODO include time and amount of sold items to featurelist
        model_products = dict()
        for product_id in features:
            data = features[product_id].dropna()
            x = data[['amount_of_all_competitors',
                      'average_price_on_market',
                      'distance_to_cheapest_competitor',
                      'price_rank',
                      'quality_rank',
                      ]]
            y = data['sold'].copy()
            y[y > 1] = 1

            model = LogisticRegression()
            model.fit(x, y)

            model_products[product_id] = model
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
