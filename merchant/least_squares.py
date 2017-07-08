import argparse
import bisect
import copy
import math
import sys
import threading

from merchant.csv_reader_ls import CSVReader
from merchant.utils import download_data

sys.path.append('./')
sys.path.append('../')
from merchant.merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant.merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant.merchant_sdk.models import Offer

from scipy.optimize import fmin

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

        # enable/disable describing variables
        self.enable_price = True
        self.enable_rank = False

        # further settings
        self.enable_predicting_sales_from_market_situation = False
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

        self.csv_reader = CSVReader()

        self.market_situation = []
        self.buy_offer = []
        self.market_situation_at_time = {}
        self.buy_offer_at_time = {}
        self.csv_merchant_id = 0
        self.newest_bo_timestamp = None
        self.newest_ms_timestamp = None

        self.x_prices = {}
        self.x_rank = {}
        self.read_csv_file()

        thread = threading.Thread(target=self.init_training, args=())
        thread.start()
        # self.init_training()

        '''
            Start Logic Loop
        '''
        self.run_logic_loop()

    def read_csv_file(self):
        print("Read csv files...")
        print("Read buyOffer.csv")
        self.csv_reader.read_buy_offer()
        print("Read marketSituation.csv")
        self.csv_reader.read_market_situation()
        self.buy_offer = self.csv_reader.buy_offer
        self.market_situation = self.csv_reader.market_situation
        self.market_situation_at_time = self.csv_reader.market_situation_at_time
        self.buy_offer_at_time = self.csv_reader.buy_offer_at_time
        self.csv_merchant_id = self.csv_reader.csv_merchant_id
        print("Finished reading csv files!")

    def init_training(self):
        print("Start initial training...")
        self.x_prices = {}
        for bo_entry in self.buy_offer:
            self.update_training_data_from_buy_offer(bo_entry)
        if self.enable_predicting_sales_from_market_situation:
            self.update_training_data_from_market_situation(self.market_situation, self.market_situation_at_time)
        print("Finished initial training!")

    def f(self, x, x_values):
        result = 0
        for value in x_values:
            result += math.pow((float(x[0]) - float(value)), 2)
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
            print("Sold offer: {}".format(offer))
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
            print("Update training data")
            self.update_training_data()
            print("get offers")
            offers = self.marketplace_api.get_offers()
            print("set missing offers")
            missing_offers = self.settings["initialProducts"] - len(self.offers)

            print("process products")
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
        if product_id in self.x_prices.keys():
            print("Calculate price on historic data...")
            if self.enable_price:
                new_price = float(fmin(self.f, 0, (self.x_prices[product_id],)))
            if self.enable_rank:
                new_rank = int(fmin(self.f, 0, (self.x_rank[product_id],)))
        else:
            print("Calculate price on purchase price...")
            if self.enable_price:
                new_price = purchase_price * 1.7
            if self.enable_rank:
                new_rank = 1

        if self.enable_price:
            print("New Price: {}".format(new_price))

        if self.enable_rank:
            print("New Rank: {}".format(new_rank))
            rank = self.get_rank(new_price, product_id, marketplace_offers)
            print("Real Rank: {}".format(rank))

        price_factor = 1.3
        if new_price is None or new_price < (purchase_price * price_factor):
            new_price = purchase_price * price_factor

        return new_price

    def add_new_product_to_offers(self, new_product, marketplace_offers):
        print("Add new product to offers: {}".format(new_product))
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
        print("Start updating training data...")
        downloaded_csvs = download_data(merchant_token)
        print("Downloaded training data!")
        if downloaded_csvs is None:
            return
        new_market_situation = downloaded_csvs['marketSituation'].to_records()
        new_buy_offer = downloaded_csvs['buyOffer'].to_records()
        ms_to_append = self.csv_reader.read_kafka_market_situation(new_market_situation)
        bo_to_append = self.csv_reader.read_kafka_buy_offer(new_buy_offer)
        self.update_ms_training_data(ms_to_append)
        self.update_bo_training_data(bo_to_append)

    def update_ms_training_data(self, downloaded_ms_data):
        print("Process downloaded market situation from kafka...")
        timestamps_of_new_ms = []
        for ms in downloaded_ms_data:
            if ms.timestamp_object not in timestamps_of_new_ms and ms.timestamp_object not in self.market_situation_at_time:
                timestamps_of_new_ms.append(ms.timestamp_object)
                self.market_situation.append(ms)
                self.market_situation_at_time[ms.timestamp_object] = []
                self.market_situation_at_time[ms.timestamp_object].append(ms)
                if self.enable_predicting_sales_from_market_situation:
                    self.update_training_data_from_market_situation([ms])
            elif ms.timestamp_object in timestamps_of_new_ms:
                self.market_situation.append(ms)
                self.market_situation_at_time[ms.timestamp_object].append(ms)
                if self.enable_predicting_sales_from_market_situation:
                    self.update_training_data_from_market_situation([ms])
        print("Finished updating MS training data from kafka!")

    def update_bo_training_data(self, downloaded_bo_data):
        print("Process downloaded buyOffer from kafka...")
        timestamps_of_new_bo = []
        for bo in downloaded_bo_data:
            if bo.timestamp_object not in timestamps_of_new_bo and bo.timestamp_object not in self.buy_offer_at_time:
                timestamps_of_new_bo.append(bo.timestamp_object)
                self.buy_offer.append(bo)
                self.buy_offer_at_time[bo.timestamp_object] = []
                self.buy_offer_at_time[bo.timestamp_object].append(bo)
                self.update_training_data_from_buy_offer(bo)
            elif bo.timestamp_object in timestamps_of_new_bo:
                self.buy_offer.append(bo)
                self.buy_offer_at_time[bo.timestamp_object].append(bo)
                self.update_training_data_from_buy_offer(bo)
        print("Finished updating BO training data from kafka!")

    def update_training_data_from_buy_offer(self, bo):
        # print("Update training data from buyOffer...")
        # prices
        if self.enable_price:
            if bo.product_id not in self.x_prices:
                self.x_prices[bo.product_id] = []

        # rank
        if self.enable_rank:
            if bo.product_id not in self.x_rank:
                self.x_rank[bo.product_id] = []
            self.x_prices[bo.product_id].append(bo.price)
            ms = self.get_market_situation_for_timestamp(bo.timestamp_object)
            rank = self.get_rank(bo.price, bo.product_id, ms)
            self.x_rank[bo.product_id].append(rank)
        # print("Finished updating training data from buyBuffer!")

    def update_training_data_from_market_situation(self, market_situation, market_situation_at_time=None):
        for ms in market_situation:
            previous_ms = self.find_previous_ms(market_situation, market_situation_at_time, ms.product_id, ms.merchant_id, ms.timestamp_object)
            if previous_ms is None and self.market_situation != market_situation:
                previous_ms = self.find_previous_ms(self.market_situation, self.market_situation_at_time, ms.product_id, ms.merchant_id, ms.timestamp_object, 20)
            if previous_ms is None:
                continue

            amount_sum = 0
            for pms in previous_ms:
                amount_sum += int(pms.amount)
            if int(amount_sum) > int(ms.amount):
                for pms in previous_ms:
                    self.update_training_data_from_buy_offer(pms)

    def find_previous_ms(self, market_situation, market_situation_at_time, product_id, merchant_id, timestamp, limit=-1):
        # print("Looking for previous market situation...")
        if market_situation_at_time is not None:
            ms_key_list = list(market_situation_at_time.keys())
            i = bisect.bisect_left(ms_key_list, timestamp) - 1
            # print("result from bisect: {}".format(i))
            if i != -1:
                prev = self.get_entries_from_market_situation(market_situation_at_time[ms_key_list[i]], product_id, merchant_id)
                # print("ts from bisect: {}".format(prev))
                return prev
            # else:
            #     print("ts from bisect is None")
        return None

    def get_entries_from_market_situation(self, market_situations, product_id, merchant_id):
        result = []
        for ms in market_situations:
            if ms.product_id == product_id and ms.merchant_id == merchant_id:
                result.append(ms)
        return result

    def get_rank(self, new_price, product_id, marketplace_offers):
        rank = 1
        for offer in marketplace_offers:
            if offer.product_id == product_id and offer.price < new_price:
                rank += 1
        return rank

    def get_market_situation_for_timestamp(self, timestamp):
        market_situation_at_time = copy.deepcopy(dict(self.market_situation_at_time))
        # print("Get market situation for timestamp...")
        last_timestamp_before = None
        last_timestamp_before_str = None
        for ts in market_situation_at_time.keys():
            if ts <= timestamp and (last_timestamp_before is None or last_timestamp_before < ts):
                last_timestamp_before = ts
                last_timestamp_before_str = ts
            elif ts > timestamp:
                break
        # print("Found market situation for timestamp: {}".format(self.market_situation_at_time[last_timestamp_before_str]))
        return market_situation_at_time[last_timestamp_before_str]


merchant_logic = LeastSquares()
merchant_server = MerchantServer(merchant_logic)
app = merchant_server.app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant using least squares')
    parser.add_argument('--port', type=int,
                        help='port to bind flask App to')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
