import datetime
import logging
import os
import random
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from SuperMerchant import SuperMerchant
from merchant_sdk.models import Offer
from training_data import TrainingData
from utils import extract_features
from utils import save_training_data, load_history


class MLMerchant(ABC, SuperMerchant):
    def __init__(self, settings):
        super().__init__(settings)
        if os.path.isfile(self.settings["data_file"]):
            self.machine_learning()
            self.last_learning = datetime.datetime.now()
        else:
            self.initial_learning()

        self.run_logic_loop()

    def initial_learning(self):
        self.training_data = TrainingData(self.merchant_token, self.merchant_id)
        self.training_data.append_by_csvs('../data/marketSituation.csv', '../data/buyOffer.csv',
                                          self.settings["initial_merchant_id"])
        # self.training_data.append_by_csvs('../data/ms1.csv', '../data/bo1.csv',
        #                                   self.settings["initial_merchant_id"])
        # self.training_data.append_by_csvs('../data/ms2.csv', '../data/bo2.csv',
        #                                   self.settings["initial_merchant_id"])

        save_training_data(self.training_data, self.settings["data_file"])
        self.train_model(self.training_data.convert_training_data())
        self.last_learning = datetime.datetime.now()

    def machine_learning(self):
        self.machine_learning_worker()
        # p = Process(target=self.machine_learning_worker)
        # p.start()
        # p.join()

    def machine_learning_worker(self):
        self.training_data = load_history(self.settings["data_file"])
        self.training_data.append_by_kafka()
        save_training_data(self.training_data, self.settings["data_file"])
        self.train_model(self.training_data.convert_training_data())
        self.last_learning = datetime.datetime.now()

    def execute_logic(self):
        next_training_session = self.last_learning \
                                + datetime.timedelta(minutes=self.settings["learning_interval"])
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
        missing_offers = self.settings["max_amount_of_offers"] - sum(offer.amount for offer in own_offers)

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
                    offer.shipping_time['standard'] = self.settings["shipping"]
                    offer.shipping_time['prime'] = self.settings["primeShipping"]
                    offer.merchant_id = self.merchant_id
                    offer.price = self.calculate_optimal_price(product, product_prices_by_uid, offer, current_offers=offers + [offer])
                    try:
                        self.marketplace_api.add_offer(offer)
                    except Exception as e:
                        print('error on adding an offer to the marketplace:', e)
            except Exception as e:
                print('could not handle product:', product, e)

        return max(1.0, request_count) / self.settings["max_req_per_sec"]

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
            # model = self.product_models[str(product.product_id)]
            # offer_list = [[x.offer_id,
            #                x.price,
            #                x.quality] for x in current_offers]
            # offer_list = [Offer(x.offer_id, x.price, x.quality) for x in current_offers]
            offer_list = current_offers

            potential_prices = list(range(1, 100, 1))
            # lst = self.create_prediction_data(offer, offer_list, potential_prices, price)
            lst = self.create_prediction_data(offer, offer_list, potential_prices, price)

            probas = self.predict(str(product.product_id), lst)
            # import pdb;pdb.set_trace()

            expected_profits = []
            for i, proba in enumerate(probas):
                expected_profits.append(proba * (potential_prices[i] - price))
            print(potential_prices[expected_profits.index(max(expected_profits))])
            return potential_prices[expected_profits.index(max(expected_profits))]
        except (KeyError, ValueError, AttributeError):
            # Fallback for new porduct
            print("RANDOMMMMMMMMM")
            return price * (np.random.exponential() + 0.99)

    def create_prediction_data(self, own_offer, offer_list: List[Offer], potential_prices: List[int], price: float):
        lst = []
        for potential_price in potential_prices:
            potential_price_candidate = potential_price / 10.0
            potential_price = price + potential_price_candidate

            setattr(next(offer for offer in offer_list if offer.offer_id == own_offer.offer_id), "price", potential_price)
            prediction_data = extract_features(own_offer.offer_id, offer_list)
            lst.append(prediction_data)
        return lst

    @abstractmethod
    def train_model(self, features):
        pass

    @abstractmethod
    def predict(self, product_id, situations):
        pass
