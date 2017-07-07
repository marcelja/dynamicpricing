from SuperMerchant import SuperMerchant
import os
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.models import Offer
import argparse
import pickle
from utils import download_data_and_aggregate, learn_from_csvs, extract_features_from_offer_snapshot, TrainingData, calculate_performance, extract_features
from sklearn.linear_model import LogisticRegression
import datetime
import logging
import pandas as pd
import numpy as np
import random
from multiprocessing import Process


MODELS_FILE = 'log_reg_models.pkl'

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl'

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


def save_training_data(data):
    with open(MODELS_FILE, 'wb') as m:
        pickle.dump(data, m)


class MLMerchant(SuperMerchant):
    def __init__(self):
        super().__init__(merchant_token, settings)
        if os.path.isfile(MODELS_FILE):
            self.machine_learning()
            self.last_learning = datetime.datetime.now()
        else:
            self.initial_learning()
        self.run_logic_loop()

    def initial_learning(self):
        self.training_data = TrainingData(self.merchant_token, self.merchant_id)
        self.training_data.append_by_csvs('../data/marketSituation.csv', '../data/buyOffer.csv',
                                          'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=')
        # self.training_data.append_by_csvs('../data/ms1.csv', '../data/bo1.csv',
        #                                   'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=')
        # self.training_data.append_by_csvs('../data/ms2.csv', '../data/bo2.csv',
        #                                   'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=')

        save_training_data(self.training_data)
        self.product_models = self.train_model(self.training_data.convert_training_data())
        self.last_learning = datetime.datetime.now()

    def machine_learning(self):
        self.machine_learning_worker()
        # p = Process(target=self.machine_learning_worker)
        # p.start()
        # p.join()

    def machine_learning_worker(self):
        self.training_data = load_history()
        self.training_data.append_by_kafka()
        save_training_data(self.training_data)
        self.product_models = self.train_model(self.training_data.convert_training_data())
        self.last_learning = datetime.datetime.now()

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
                own_offer.price = self.calculate_optimal_price(own_offer, product_prices_by_uid, own_offer, current_offers=offers)
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
                    offer.price = self.calculate_optimal_price(product, product_prices_by_uid, offer, current_offers=offers)
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
                    offer.price = self.calculate_optimal_price(product, product_prices_by_uid, offer, current_offers=offers+[offer])
                    try:
                        self.marketplace_api.add_offer(offer)
                    except Exception as e:
                        print('error on adding an offer to the marketplace:', e)
            except Exception as e:
                print('could not handle product:', product, e)

        return max(1.0, request_count) / settings['max_req_per_sec']

    def calculate_optimal_price(self, product, product_prices_by_uid, offer, current_offers=None):
        """
        Computes a price for a product based on trained models or (exponential) random fallback
        :param product: product object that is to be priced
        :param current_offers: list of offers
        :return:
        """

        # TODO split this function into two or three

        price = product_prices_by_uid[product.uid]

        if random.uniform(0, 1) < 0.3:
            print("RAND \n\n\n\n\n")
            return (random.randint(price * 100, 10000) / 100)
        try:
            # TODO Add actual product id
            model = self.product_models['1']
            # model = self.product_models[str(product.product_id)]
            offer_list = [[x.offer_id,
                           x.price,
                           x.quality] for x in current_offers]
            lst = []
            potential_prices = list(range(1, 100, 1))
            for potential_price in potential_prices:
                potential_price_candidate = potential_price / 10.0
                potential_price = price + potential_price_candidate

                next(x for x in offer_list if x[0] == offer.offer_id)[1] = potential_price
                prediction_data = extract_features(offer.offer_id, offer_list)
                lst.append(prediction_data)
            probas = model.predict_proba(lst)[:, 1]
            expected_profits = []
            for i, proba in enumerate(probas):
                expected_profits.append(proba * (potential_prices[i] - price))
            print(potential_prices[expected_profits.index(max(expected_profits))])
            return potential_prices[expected_profits.index(max(expected_profits))]
        except (KeyError, ValueError, AttributeError):
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
                        default=5100,
                        help='Port to bind flask App to, default is 5101')
    args = parser.parse_args()
    server = MerchantServer(MLMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
