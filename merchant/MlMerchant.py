import copy
import datetime
import logging
import os
import random
import sys
from abc import ABC, abstractmethod
from threading import Thread, Lock
from typing import List

from numpy import arange
from sklearn.linear_model import LogisticRegression

from SuperMerchant import SuperMerchant
from merchant_sdk.models import Offer, Product
from training_data import TrainingData
from utils import extract_features, save_training_data, load_history, calculate_performance, NUM_OF_UNIVERSAL_FEATURES

CALCULATE_PERFORMANCE = True


class MLMerchant(ABC, SuperMerchant):
    def __init__(self, settings):
        super().__init__(settings)
        self.model = dict()
        self.last_learning = None
        if os.path.isfile(self.settings["data_file"]):
            self.machine_learning()
        else:
            self.initial_learning()

        self.run_logic_loop()

    def initial_learning(self):
        self.training_data = TrainingData(self.merchant_token, self.merchant_id)
        self.training_data.append_by_csvs('../data/marketSituation.csv', '../data/buyOffer.csv',
                                          self.settings["initial_merchant_id"])
        save_training_data(self.training_data, self.settings["data_file"])
        self.model = self.train_model(self.training_data.convert_training_data())
        self.universal_model = self.train_universal_model(self.training_data.convert_training_data(True))
        self.calc_performance(self.training_data)
        self.last_learning = datetime.datetime.now()

    def calc_performance(self, training_data: TrainingData):
        if not CALCULATE_PERFORMANCE:
            return
        sales_probabilities = []
        sales = []
        for joined_market_situations in training_data.joined_data.values():
            for jms in joined_market_situations.values():
                if self.merchant_id in jms.merchants:
                    for offer_id in jms.merchants[self.merchant_id].keys():
                        amount_sales = TrainingData.extract_sales(jms.merchants[self.merchant_id][offer_id].product_id, offer_id, jms.sales)
                        features = extract_features(offer_id, TrainingData.create_offer_list(jms), True, training_data.product_prices)
                        if amount_sales == 0:
                            sales.append(0)
                            # sales_probabilities.append(self.predict_with_universal_model([features]))
                            sales_probabilities.append(self.predict_with_universal_model([features]))
                        else:
                            for i in range(amount_sales):
                                sales.append(1)
                                # sales_probabilities.append(self.predict_with_universal_model([features]))
                                sales_probabilities.append(self.predict_with_universal_model([features]))
        calculate_performance(sales_probabilities, sales, NUM_OF_UNIVERSAL_FEATURES)

    def machine_learning(self):
        thread = Thread(target=self.machine_learning_worker)
        thread.start()

    def machine_learning_worker(self):
        self.training_data: TrainingData = load_history(self.settings["data_file"])
        self.training_data.append_by_kafka()
        save_training_data(self.training_data, self.settings["data_file"])
        product_models = self.train_model(self.training_data.convert_training_data())
        universal_model: LogisticRegression = self.train_universal_model(self.training_data.convert_training_data(True))
        lock = Lock()
        lock.acquire()
        self.model = product_models
        self.universal_model: LogisticRegression = universal_model
        lock.release()
        self.calc_performance(self.training_data)
        self.last_learning = datetime.datetime.now()

    def execute_logic(self):
        self.perform_learning_if_necessary()
        request_count = 0

        # get and process existing offers
        offers = self.get_offers()
        own_offers = [offer for offer in offers if offer.merchant_id == self.merchant_id]
        own_offers_by_uid = {offer.uid: offer for offer in own_offers}
        missing_offers = self.settings["max_amount_of_offers"] - sum(offer.amount for offer in own_offers)

        # buy new products
        new_products = self.buy_new_products(missing_offers)
        product_prices_by_uid = self.get_product_prices()

        # handle bought products and either add them to existing offers or create new ones
        request_count = self.update_existing_offers(offers, own_offers, product_prices_by_uid, request_count)
        request_count = self.process_bought_products(new_products, offers, own_offers_by_uid, product_prices_by_uid, request_count)

        return max(1.0, request_count) / self.settings["max_req_per_sec"]

    def get_product_prices(self):
        try:
            products = self.producer_api.get_products()
            product_prices_by_uid = {product.uid: product.price for product in products}
            return product_prices_by_uid
        except Exception as e:
            logging.warning('Could not buy receive products from producer api: {}'.format(e))
        return dict()

    def process_bought_products(self, new_products: List[Product], offers: List[Offer], own_offers_by_uid: dict, product_prices_by_uid: dict, request_count: int):
        for product in new_products:
            try:
                if product.uid in own_offers_by_uid:
                    request_count = self.update_existing_offer(offers, own_offers_by_uid, product, product_prices_by_uid, request_count)
                else:
                    self.create_new_offer(offers, product, product_prices_by_uid)
            except Exception as e:
                print('could not handle product:', product, e)
        return request_count

    def create_new_offer(self, offers: List[Offer], product: Product, product_prices_by_uid: dict):
        offer = Offer.from_product(product)
        offer.prime = True
        offer.shipping_time['standard'] = self.settings["shipping"]
        offer.shipping_time['prime'] = self.settings["primeShipping"]
        offer.merchant_id = self.merchant_id
        offer.price = self.calculate_optimal_price(product_prices_by_uid, offer, current_offers=offers + [offer], product=product)
        try:
            self.marketplace_api.add_offer(offer)
        except Exception as e:
            print('error on adding an offer to the marketplace:', e)

    def update_existing_offer(self, offers: List[Offer], own_offers_by_uid: dict, product: Product, product_prices_by_uid: dict, request_count: int):
        offer = own_offers_by_uid[product.uid]
        offer.amount += product.amount
        offer.signature = product.signature
        try:
            self.marketplace_api.restock(offer.offer_id, amount=product.amount, signature=product.signature)
        except Exception as e:
            print('error on restocking an offer:', e)
        offer.price = self.calculate_optimal_price(product_prices_by_uid, offer, current_offers=offers, product=product)
        try:
            self.marketplace_api.update_offer(offer)
            request_count += 1
        except Exception as e:
            print('error on updating an offer:', e)
        return request_count

    def update_existing_offers(self, offers: List[Offer], own_offers: List[Offer], product_prices_by_uid: dict, request_count: int):
        for own_offer in own_offers:
            if own_offer.amount > 0:
                # only update an existing offer, when new price is different from existing one
                old_price = own_offer.price
                own_offer.price = self.calculate_optimal_price(product_prices_by_uid, own_offer, current_offers=offers)
                if float(own_offer.price) != float(old_price):
                    try:
                        self.marketplace_api.update_offer(own_offer)
                        request_count += 1
                    except Exception as e:
                        logging.warning('Could not update offer on marketplace: {}'.format(e))
        return request_count

    def buy_new_products(self, missing_offers: int):
        new_products = []
        for _ in range(missing_offers):
            try:
                prod = self.producer_api.buy_product()
                new_products.append(prod)
            except Exception as e:
                logging.warning('Could not buy new product from producer api: {}'.format(e))
                raise e
        return new_products

    def get_offers(self):
        try:
            return self.marketplace_api.get_offers(include_empty_offers=False)
        except Exception as e:
            logging.warning('Could not receive offers from marketplace: {}'.format(e))
            raise e

    def perform_learning_if_necessary(self):
        if self.last_learning:
            next_training_session = self.last_learning + datetime.timedelta(minutes=self.settings["learning_interval"])
        if not self.last_learning or next_training_session <= datetime.datetime.now():
            self.last_learning = datetime.datetime.now()
            self.machine_learning()

    def calculate_optimal_price(self, product_prices_by_uid: dict, offer: Offer, current_offers: List[Offer] = None, product: Product = None):
        """
        Computes a price for a product based on trained models or (exponential) random fallback
        :param product: product object that is to be priced
        :param current_offers: list of offers
        :return:
        """

        price = product_prices_by_uid[offer.uid]
        if random.uniform(0, 1) < 0.01:
            print('r', end='')
            sys.stdout.flush()
            return self.random_price(price)
        else:
            return self.ml_highest_profit(current_offers, offer, price)

    def ml_highest_profit(self, current_offers: List[Offer], offer: Offer, price: float):
        try:
            potential_prices = list(arange(price * 0.9, price * 3, 0.5))

            if str(offer.product_id) in self.model:
                lst = self.create_prediction_data(offer, current_offers, potential_prices, price, False)
                probas = self.predict(str(offer.product_id), lst)
                print('.', end='')
                sys.stdout.flush()
            else:
                lst = self.create_prediction_data(offer, current_offers, potential_prices, price, True)
                probas = self.predict_with_universal_model(lst)
                print('U', end='')
                sys.stdout.flush()

            expected_profits = self.calculate_expected_profits(potential_prices, price, probas)

            best_price = potential_prices[expected_profits.index(max(expected_profits))]

            return best_price
        except (KeyError, ValueError, AttributeError) as e:
            # Fallback for new products
            print('R', end='')
            print(e)
            sys.stdout.flush()
            return self.random_price(price)

    def random_price(self, price: float):
        return round(price * random.uniform(1.01, 3), 2)

    def calculate_expected_profits(self, potential_prices: List[float], price: float, probas: List):
        return [(proba * (potential_prices[i] - price)) for i, proba in enumerate(probas)]

    def create_prediction_data(self, own_offer: Offer, current_offers: List[Offer], potential_prices: List[int], price: float, universal_features: bool):
        lst = []
        for potential_price in potential_prices:
            potential_price_candidate = potential_price / 10.0
            potential_price = price + potential_price_candidate

            setattr(next(offer for offer in current_offers if offer.offer_id == own_offer.offer_id), "price", potential_price)
            prediction_data = extract_features(own_offer.offer_id, current_offers, universal_features, self.training_data.product_prices)
            lst.append(prediction_data)
        return lst

    @abstractmethod
    def train_model(self, features):
        pass

    @abstractmethod
    def train_universal_model(self, features: dict):
        pass

    @abstractmethod
    def train_universal_statsmodel(self, features: dict):
        pass

    @abstractmethod
    def predict(self, product_id: str, situations: List[List[int]]):
        pass

    @abstractmethod
    def predict_with_universal_model(self, situations: List[List[int]]):
        pass

    @abstractmethod
    def predict_with_universal_statsmodel(self, situations: List[List[int]]):
        pass
