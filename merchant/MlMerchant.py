import datetime
import logging
import os
import random
import sys
from threading import Thread
from typing import List, Dict

from SuperMerchant import SuperMerchant
from apiabstraction import ApiAbstraction
from merchant_sdk.models import Offer, Product
from ml_engine import MlEngine
from training_data import TrainingData
from utils.feature_extractor import extract_features
from utils.performance_calculator import PerformanceCalculator
from utils.prices import PriceUtils
from utils.utils import save_training_data, load_history


class MLMerchant(SuperMerchant):
    def __init__(self, settings, ml_engine: MlEngine, api: ApiAbstraction = None):
        super().__init__(settings, api)
        self.last_learning = None
        self.ml_engine: MlEngine = ml_engine
        self.performance_calculator = PerformanceCalculator(ml_engine, self.merchant_id)
        self.training_data: TrainingData = None
        self.priceutils = PriceUtils()

    def initialize(self):
        if self.settings["data_file"] is not None and os.path.isfile(self.settings["data_file"]):
            self.update_machine_learning()
        else:
            self.initial_learning()

        self.run_logic_loop()

    def update_machine_learning(self):
        thread = Thread(target=self.machine_learning_worker)
        thread.start()

    def machine_learning_worker(self):
        self.load_and_update_training_data()
        self.perform_learning()
        self.performance_calculator.calc_performance(self.training_data, self.merchant_id)

    def initial_learning(self):
        self.create_training_data()
        self.perform_learning()
        self.performance_calculator.calc_performance(self.training_data, self.merchant_id)
        logging.debug('Setup done. Starting merchant...')

    def perform_learning(self):
        self.ml_engine.train_model(self.training_data.convert_training_data())
        self.ml_engine.train_universal_model(self.training_data.convert_training_data(True))
        self.last_learning = datetime.datetime.now()

    def create_training_data(self):
        self.training_data = TrainingData(self.merchant_token, self.merchant_id)
        self.training_data.append_by_csvs(self.settings['market_situation_csv_path'],
                                          self.settings['buy_offer_csv_path'],
                                          self.settings["initial_merchant_id"])
        save_training_data(self.training_data, self.settings["data_file"])

    def load_and_update_training_data(self):
        self.training_data = load_history(self.settings["data_file"])
        self.training_data.merchant_token = self.merchant_token
        self.training_data.append_by_kafka(self.settings["kafka_reverse_proxy_url"])
        save_training_data(self.training_data, self.settings["data_file"])

    def execute_logic(self):
        self.perform_learning_if_necessary()
        self.api.reset_request_counter()

        # get and process existing offers
        offers = self.api.get_offers()
        own_offers = [offer for offer in offers if offer.merchant_id == self.merchant_id]
        own_offers_by_uid = {offer.uid: offer for offer in own_offers}
        missing_offers = self.settings["max_amount_of_offers"] - sum(offer.amount for offer in own_offers)

        # buy new products
        new_products = self.buy_new_products(missing_offers)
        product_prices_by_uid = self.get_product_prices()

        # handle bought products and either add them to existing offers or create new ones
        self.update_existing_offers(offers, own_offers, product_prices_by_uid)
        self.process_bought_products(new_products, offers, own_offers_by_uid, product_prices_by_uid)

        return max(1.0, self.api.request_counter) / self.settings["max_req_per_sec"]

    def get_product_prices(self) -> Dict[str, float]:
        products = self.api.get_products()
        return {product.uid: product.price for product in products}

    def process_bought_products(self, new_products: List[Product], offers: List[Offer], own_offers_by_uid: dict, product_prices_by_uid: dict):
        for product in new_products:
            self.process_bought_product(offers, own_offers_by_uid, product, product_prices_by_uid)

    def process_bought_product(self, offers, own_offers_by_uid, product, product_prices_by_uid):
        try:
            if product.uid in own_offers_by_uid:
                self.update_existing_offer(offers, own_offers_by_uid, product, product_prices_by_uid)
            else:
                self.create_new_offer(offers, product, product_prices_by_uid)
        except Exception as e:
            print('could not handle product:', product, e)

    def create_new_offer(self, offers: List[Offer], product: Product, product_prices_by_uid: dict):
        offer = Offer.from_product(product)
        offer.prime = True
        offer.shipping_time['standard'] = self.settings["shipping"]
        offer.shipping_time['prime'] = self.settings["primeShipping"]
        offer.merchant_id = self.merchant_id
        offer.price = self.calculate_optimal_price(product_prices_by_uid, offer, product.uid, current_offers=offers + [offer])
        self.api.add_offer(offer)

    def update_existing_offer(self, offers: List[Offer], own_offers_by_uid: dict, product: Product, product_prices_by_uid: dict):
        offer = own_offers_by_uid[product.uid]
        offer.amount += product.amount
        offer.signature = product.signature
        self.api.restock(offer.offer_id, amount=product.amount, signature=product.signature)
        offer.price = self.calculate_optimal_price(product_prices_by_uid, offer, product.uid, current_offers=offers)
        self.api.update_offer(offer)

    def update_existing_offers(self, offers: List[Offer], own_offers: List[Offer], product_prices_by_uid: dict):
        for own_offer in own_offers:
            if own_offer.amount > 0:
                # only update an existing offer, when new price is different from existing one
                old_price = own_offer.price
                own_offer.price = self.calculate_optimal_price(product_prices_by_uid, own_offer, own_offer.uid, current_offers=offers)
                if float(own_offer.price) != float(old_price):
                    self.api.update_offer(own_offer)

    def buy_new_products(self, missing_offers: int):
        new_products = []
        for _ in range(missing_offers):
            prod = self.api.buy_product()
            new_products.append(prod)
        return new_products

    def perform_learning_if_necessary(self):
        if self.last_learning:
            next_training_session = self.last_learning + datetime.timedelta(minutes=self.settings["learning_interval"])
        if not self.last_learning or next_training_session <= datetime.datetime.now():
            self.last_learning = datetime.datetime.now()
            self.update_machine_learning()

    def calculate_optimal_price(self, product_prices_by_uid: dict, own_offer: Offer, uid, current_offers: List[Offer] = None):
        price = product_prices_by_uid[uid]
        if random.uniform(0, 1) < 0.01 or self.training_data.number_marketsituations < self.settings["min_marketsituations"]:
            print('r', end='')
            sys.stdout.flush()
            return self.priceutils.random_price(price)
        else:
            return self.highest_profit_from_ml(current_offers, own_offer, price)

    def highest_profit_from_ml(self, current_offers: List[Offer], own_offer: Offer, price: float):
        try:
            potential_prices = self.priceutils.get_potential_prices(price, False)
            if str(own_offer.product_id) in self.ml_engine.product_model_dict:
                probas = self.__highest_profit_from_product_model(current_offers, own_offer, potential_prices, price)
            else:
                probas = self.__highest_profit_from_universal_model(current_offers, own_offer, potential_prices, price)
            expected_profits = self.priceutils.calculate_expected_profits(potential_prices, price, probas)
            best_price = potential_prices[expected_profits.index(max(expected_profits))]
            return best_price
        except (KeyError, ValueError, AttributeError) as e:
            raise e
            # Fallback for new products
            print('R', end='')
            print(e)
            sys.stdout.flush()
            return self.priceutils.random_price(price)

    def __highest_profit_from_universal_model(self, current_offers, own_offer, potential_prices, price):
        lst = self.__create_prediction_data(own_offer, current_offers, potential_prices, price, True)
        probas = self.ml_engine.predict_with_universal_model(lst)
        print('U', end='')
        sys.stdout.flush()
        return probas

    def __highest_profit_from_product_model(self, current_offers, own_offer, potential_prices, price):
        lst = self.__create_prediction_data(own_offer, current_offers, potential_prices, price, False)
        probas = self.ml_engine.predict(str(own_offer.product_id), lst)
        print('.', end='')
        sys.stdout.flush()
        return probas

    def __create_prediction_data(self, own_offer: Offer, current_offers: List[Offer], potential_prices: List[int], price: float, universal_features: bool):
        lst = []
        for potential_price in potential_prices:
            potential_price_candidate = potential_price / 10.0
            potential_price = price + potential_price_candidate

            setattr(next(offer for offer in current_offers if offer.offer_id == own_offer.offer_id), "price", potential_price)
            prediction_data = extract_features(own_offer.offer_id, current_offers, universal_features, self.training_data.product_prices)
            lst.append(prediction_data)
        return lst
