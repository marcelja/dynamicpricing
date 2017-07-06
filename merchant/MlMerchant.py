from SuperMerchant import SuperMerchant
import os
from merchant_sdk.models import Offer
from utils import TrainingData, extract_features, save_training_data, load_history
import datetime
import logging
import numpy as np
import random
from multiprocessing import Process
from abc import ABC, abstractmethod


class MLMerchant(ABC, SuperMerchant):
    def __init__(self, merchant_token, settings):
        super().__init__(merchant_token, settings)
        self.data_file = self.settings['data_file']
        if os.path.isfile(self.data_file):
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

        save_training_data(self.training_data, self.data_file)
        self.train_model(self.training_data.convert_training_data())
        self.last_learning = datetime.datetime.now()

    def machine_learning(self):
        self.machine_learning_worker()
        # p = Process(target=self.machine_learning_worker)
        # p.start()
        # p.join()

    def machine_learning_worker(self):
        self.training_data = load_history(self.data_file)
        self.training_data.append_by_kafka()
        save_training_data(self.training_data, self.data_file)
        self.train_model(self.training_data.convert_training_data())
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
        missing_offers = self.settings['max_amount_of_offers'] - sum(offer.amount for offer in own_offers)

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

        return max(1.0, request_count) / self.settings['max_req_per_sec']

    def calculate_optimal_price(self, product, product_prices_by_uid, offer, current_offers=None):
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
            # model = self.product_models[str(product.product_id)]
            offer_list = [[x.offer_id,
                           x.price,
                           x.quality] for x in current_offers]


            # offer_df = offer_df[offer_df['product_id'] == product.product_id]
            # own_offers_mask = offer_df['merchant_id'] == self.merchant_id

            # features = []
            lst = []
            potential_prices = list(range(1, 100, 1))
            for potential_price in potential_prices:

                potential_price_candidate = potential_price / 10.0
                potential_price = price + potential_price_candidate

                next(x for x in offer_list if x[0] == offer.offer_id)[1] = potential_price
                prediction_data = extract_features(offer.offer_id, offer_list)
                lst.append(prediction_data)

            probas = self.predict(str(product.product_id), lst)
            # import pdb;pdb.set_trace()

            expected_profits = []

            for i, proba in enumerate(probas):
                expected_profits.append(proba * (potential_prices[i] - price))
            print(potential_prices[expected_profits.index(max(expected_profits))])
            return potential_prices[expected_profits.index(max(expected_profits))]









                # offer_df.loc[own_offers_mask, 'price'] = potential_price
                # features.append(extract_features_from_offer_snapshot(potential_price, current_offers, self.merchant_id,
                #                                                      product.product_id))

                # probas = model.predict_proba(features)[:, 1]
                # max_expected_profit = 0
                # for i, f in enumerate(features):
                #     expected_profit = probas[i] * (f[0] - price)
                #     if expected_profit > max_expected_profit:
                #         max_expected_profit = expected_profit
                #         best_price = f[0]
                # print(best_price)
                # return best_price
        except (KeyError, ValueError, AttributeError):
            # Fallback for new porduct
            print("RANDOMMMMMMMMM")
            return price * (np.random.exponential() + 0.99)

    @abstractmethod
    def train_model(self, features):
        pass

    @abstractmethod
    def predict(self, product_id, situations):
        pass
