import argparse
import sys

from merchant.utils import download_data

sys.path.append('./')
sys.path.append('../')
from merchant.merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant.merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant.merchant_sdk.models import Offer
import numpy as np
import math
import csv
from scipy.optimize import fmin
from sklearn import linear_model

'''
    Template for Ruby deployment to insert defined tokens
'''
# merchant_token = "{{API_TOKEN}}"
# merchant_token = 'fikFWZXKVZIlioyFt3e55BSPoWUArm4XVom2OKMusegbTfqNiVRngtDWQhfIUjoz'
# merchant_token = "ng6OkL54Zv84WZSPWhjLD1mR4niOxJmmysBjFGnoCvsiUL823rNGsAhwwRMvj9hi"
merchant_token = "j6XephThMsFfkxJd5WUyV4samgUpM8z6EWj4EDlb62HqzbT58x3d2vDocheyqe55"
# merchant id: VY4gEK861EkIjiQ1YsFXak71oNKxQy3HVUNWLnjg8iY=

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'initialProducts': 5,
    'shipping': 5,
    'primeShipping': 1,
    'maxReqPerSec': 40.0,
    'underprice': 0.2
}


def get_from_list_by_key(dict_list, key, value):
    elements = [elem for elem in dict_list if elem[key] == value]
    if elements:
        return elements[0]
    return None


class LeastSquares(MerchantBaseLogic):
    def __init__(self):
        MerchantBaseLogic.__init__(self)
        global settings
        self.settings = settings

        '''
            Information store
        '''
        self.products = {}
        self.offers = {}

        '''
            Predefined API token
        '''
        self.merchant_id = settings['merchant_id']
        self.merchant_token = merchant_token

        '''
            Setup API
        '''
        PricewarsRequester.add_api_token(self.merchant_token)
        self.marketplace_api = MarketplaceApi(host=self.settings['marketplace_url'])
        self.producer_api = ProducerApi(host=self.settings['producer_url'])

        self.market_situation = []
        self.buy_offer = []
        self.market_situation_at_time = {}
        self.buy_offer_at_time = {}
        self.highest_product_price = -1
        self.lowest_product_price = -1
        self.our_merchant_id = 0

        self.x_prices = {}
        self.read_csv_file()
        self.init_training()

        '''
            Start Logic Loop
        '''
        self.run_logic_loop()

    # TODO: reading csv and grouping by timestamp can be done in one step as well...
    def read_csv_file(self):
        with open('../data/buyOffer.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                self.buy_offer.append(
                    {'amount': row[0], 'consumer_id': row[1], 'left_in_stock': row[3], 'merchant_id': row[4], 'offer_id': row[5], 'price': row[6], 'product_id': row[7],
                     'quality': row[8], 'timestamp': row[9]})
                # BUY_OFFER.append(
                #     {'amount': row[0], 'consumer_id': row[1], 'http_code': row[2], 'left_in_stock': row[3], 'merchant_id': row[4], 'offer_id': row[5], 'price': row[6], 'product_id': row[7],
                #      'quality': row[8], 'timestamp': row[9], 'uid': row[10]})
        with open('../data/marketSituation.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                self.market_situation.append(
                    {'amount': row[0], 'merchant_id': row[1], 'offer_id': row[2], 'price': row[3], 'prime': row[4], 'product_id': row[5], 'quality': row[6], 'shipping_time_prime': row[7],
                     'shipping_time_standard': row[8], 'timestamp': row[9], 'triggering_merchant_id': row[10]})
                # MARKET_SITUATION.append(
                #     {'amount': row[0], 'merchant_id': row[1], 'offer_id': row[2], 'price': row[3], 'prime': row[4], 'product_id': row[5], 'quality': row[6], 'shipping_time_prime': row[7],
                #      'shipping_time_standard': row[8], 'timestamp': row[9], 'triggering_merchant_id': row[10], 'uid': row[11]})
        self.our_merchant_id = self.buy_offer[0]['merchant_id']
        self.group_data_by_timestamp()

    def group_data_by_timestamp(self):
        for ms_entry in self.market_situation:
            if ms_entry['timestamp'] not in self.market_situation_at_time:
                self.market_situation_at_time[ms_entry['timestamp']] = []
            self.market_situation_at_time[ms_entry['timestamp']].append(ms_entry)
            if float(ms_entry['price']) > self.highest_product_price:
                self.highest_product_price = float(ms_entry['price'])
        for bo_entry in self.buy_offer:
            if bo_entry['timestamp'] not in self.buy_offer_at_time:
                self.buy_offer_at_time[bo_entry['timestamp']] = []
            self.buy_offer_at_time[bo_entry['timestamp']].append(bo_entry)
            if self.lowest_product_price == -1 or float(ms_entry['price']) < self.lowest_product_price:
                self.lowest_product_price = float(ms_entry['price'])

    def init_training(self):
        self.x_prices = {}
        for bo_entry in self.buy_offer:
            if bo_entry['product_id'] not in self.x_prices.keys():
                self.x_prices[bo_entry['product_id']] = []
            self.x_prices[bo_entry['product_id']].append(bo_entry)

    def f(self, x, product_id):
        result = 0
        for sale in self.x_prices[product_id]:
            result += math.pow((float(x[0]) - float(sale['price'])), 2)
        return result

    def update_api_endpoints(self):
        """
        Updated settings may contain new endpoints, so they need to be set in the api client as well.
        However, changing the endpoint (after simulation start) may lead to an inconsistent state
        :return: None
        """
        self.marketplace_api.host = self.settings['marketplace_url']
        self.producer_api.host = self.settings['producer_url']

    '''
        Implement Abstract methods / Interface
    '''

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        print('update settings')

        def cast_to_expected_type(key, value, def_settings=self.settings):
            if key in def_settings:
                return type(def_settings[key])(value)
            else:
                return value

        new_settings_casted = dict([
            (key, cast_to_expected_type(key, new_settings[key]))
            for key in new_settings
        ])

        self.settings.update(new_settings_casted)
        self.update_api_endpoints()
        return self.settings

    def sold_offer(self, offer):
        if self.state != 'running':
            return
        try:
            offers = self.marketplace_api.get_offers()
            self.buy_product_and_update_offer(offers)
        except Exception as e:
            print('error on handling a sold offer:', e)

    '''
        Merchant Logic for being the cheapest
    '''

    def setup(self):
        try:
            marketplace_offers = self.marketplace_api.get_offers()
            for i in range(settings['initialProducts']):
                self.buy_product_and_update_offer(marketplace_offers)
        except Exception as e:
            print('error on setup:', e)

    def execute_logic(self):
        try:
            offers = self.marketplace_api.get_offers()
            missing_offers = self.settings["initialProducts"] - len(self.offers)

            for product in self.products.values():
                if product.uid in self.offers:
                    offer = self.offers[product.uid]
                    offer.price = self.calculate_prices(offers, product.price, product.product_id)
                    try:
                        self.marketplace_api.update_offer(offer)
                    except Exception as e:
                        print('error on updating an offer:', e)
                else:
                    print('ERROR: product uid is not in offers; skipping')
        except Exception as e:
            print('error on executing the logic:', e)
        return settings['maxReqPerSec'] / 10

    def calculate_prices(self, marketplace_offers, purchase_price, product_id):
        self.update_training_data()
        if product_id in self.x_prices.keys():
            print("Calculate price on historic data...")
            new_price = float(fmin(self.f, 0, (product_id,)))
        else:
            print("Calculate price on purchase price...")
            new_price = purchase_price
        print("New Price: {}".format(new_price))

        if new_price < purchase_price:
            new_price = purchase_price

        return new_price

    def add_new_product_to_offers(self, new_product, marketplace_offers):
        new_offer = Offer.from_product(new_product)
        new_offer.price = self.calculate_prices(marketplace_offers, new_product.price, new_product.product_id)
        new_offer.shipping_time = {
            'standard': settings['shipping'],
            'prime': settings['primeShipping']
        }
        new_offer.prime = True
        try:
            new_offer.offer_id = self.marketplace_api.add_offer(new_offer).offer_id
            self.products[new_product.uid] = new_product
            self.offers[new_product.uid] = new_offer
        except Exception as e:
            print('error on adding a new offer:', e)

    def restock_existing_product(self, new_product, marketplace_offers):
        print('restock product', new_product)
        product = self.products[new_product.uid]
        product.amount += new_product.amount
        product.signature = new_product.signature

        offer = self.offers[product.uid]
        print('in this offer:', offer)
        offer.price = self.calculate_prices(marketplace_offers, product.price, product.product_id)
        offer.amount = product.amount
        offer.signature = product.signature
        try:
            self.marketplace_api.restock(offer.offer_id, new_product.amount, offer.signature)
        except Exception as e:
            print('error on restocking an offer:', e)

    def buy_product_and_update_offer(self, marketplace_offers):
        print('buy prod')
        try:
            print('buy')
            new_product = self.producer_api.buy_product()

            if new_product.uid in self.products:
                print('restock')
                self.restock_existing_product(new_product, marketplace_offers)
            else:
                print('add new')
                self.add_new_product_to_offers(new_product, marketplace_offers)
        except Exception as e:
            print('error on buying a new product:', e)

    def update_training_data(self):
        downloaded_csvs = download_data(merchant_token)
        if downloaded_csvs is None:
            return
        new_market_situation = downloaded_csvs['marketSituation'].to_records()
        new_buy_offer = downloaded_csvs['buyOffer'].to_records()
        print("")
        ms_to_append = [self.convert_kafka_market_situation_row_to_internal_object(ms) for ms in new_market_situation]
        bo_to_append = [self.convert_kafka_buy_offer_row_to_internal_object(bo) for bo in new_buy_offer]
        print("")
        print("MS length before: {}".format(len(self.market_situation)))
        print("MS_TS length before: {}".format(len(self.market_situation_at_time)))
        timestamps_of_new_ms = []
        for ms in ms_to_append:
            if ms['timestamp'] not in timestamps_of_new_ms and ms['timestamp'] not in self.market_situation_at_time.keys():
                timestamps_of_new_ms.append(ms['timestamp'])
                self.market_situation.append(ms)
                self.market_situation_at_time[ms['timestamp']] = []
                self.market_situation_at_time[ms['timestamp']].append(ms)
            elif ms['timestamp'] in timestamps_of_new_ms:
                self.market_situation.append(ms)
                self.market_situation_at_time[ms['timestamp']].append(ms)
        print("MS length after: {}".format(len(self.market_situation)))
        print("MS_TS length after: {}".format(len(self.market_situation_at_time)))
        print("BO length before: {}".format(len(self.buy_offer)))
        print("BO_TS length before: {}".format(len(self.buy_offer_at_time)))
        timestamps_of_new_bo = []
        for bo in bo_to_append:
            if bo['timestamp'] not in timestamps_of_new_bo and bo['timestamp'] not in self.buy_offer_at_time.keys():
                timestamps_of_new_bo.append(bo['timestamp'])
                self.buy_offer.append(bo)
                self.buy_offer_at_time[bo['timestamp']] = []
                self.buy_offer_at_time[bo['timestamp']].append(bo)
            elif bo['timestamp'] in timestamps_of_new_bo:
                self.buy_offer.append(bo)
                self.buy_offer_at_time[bo['timestamp']].append(bo)
        print("BO length after: {}".format(len(self.buy_offer)))
        print("BO_TS length after: {}".format(len(self.buy_offer_at_time)))

    def convert_kafka_buy_offer_row_to_internal_object(self, row):
        if row[3] != 200: # http code
            return None
        return {'amount': row[1], 'consumer_id': row[2], 'left_in_stock': row[4], 'merchant_id': row[5], 'offer_id': row[6], 'price': row[7], 'product_id': row[8], 'quality': row[9],
                'timestamp': row[10]}

    def convert_kafka_market_situation_row_to_internal_object(self, row):
        return {'amount': row[1], 'merchant_id': row[2], 'offer_id': row[3], 'price': row[4], 'prime': row[5], 'product_id': row[6], 'quality': row[7], 'shipping_time_prime': row[8],
                'shipping_time_standard': row[9], 'timestamp': row[10], 'triggering_merchant_id': row[11]}


merchant_logic = LeastSquares()
merchant_server = MerchantServer(merchant_logic)
app = merchant_server.app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant Being Cheapest')
    parser.add_argument('--port', type=int,
                        help='port to bind flask App to')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
