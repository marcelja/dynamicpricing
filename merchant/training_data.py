import bisect
import csv
import logging
from typing import List

from utils.timestamp_converter import TimestampConverter

from merchant_sdk.models import Offer
from models.joined_market_situation import JoinedMarketSituation
from utils.utils import get_buy_offer_fieldnames, get_market_situation_fieldnames
from utils.feature_extractor import extract_features
from utils.kafka_downloader import download_kafka_files


class TrainingData:
    """
    self.joined_data =
    {
        product_id: {
            timestamp: JoinedMarketSituation {
                sales: [(timestamp, offer_id), (timestamp, offer_id), ...],
                merchants: {
                    merchant_id: {
                        offer_id: Offer { price, quality, ...}
                    }
                }
            }
        }
    }
    """

    def __init__(self, merchant_token: str, merchant_id: str,
                 market_situations_json=None, sales_json=None):
        self.joined_data = {}
        self.merchant_token: str = merchant_token
        self.merchant_id: str = merchant_id
        self.timestamps: List = []
        self.last_sale_timestamp: str = None

        self.total_sale_events: int = 0
        self.sales_wo_ms: int = 0

        self.product_prices: dict = dict()  # store all prices from sales

    def update_timestamps(self):
        timestamps = set()
        for product in self.joined_data.values():
            for timestamp in product.keys():
                # TODO add at right position
                timestamps.add(timestamp)
        self.timestamps = sorted(timestamps)

    def create_training_data(self, product_id, universal_features, interval_length=5):
        product = self.joined_data[product_id]
        sales_vector = []
        features_vector = []

        for timestamp, joined_market_situation in product.items():
            offer_list = self.create_offer_list(joined_market_situation)
            self.append_to_vectors_from_features(features_vector, sales_vector, joined_market_situation, offer_list, product_id, universal_features, timestamp)

        return features_vector, sales_vector

    def append_to_vectors_from_features(self, features_vector, sales_vector, joined_market_situation: JoinedMarketSituation, offer_list, product_id, universal_features, timestamp):
        if self.merchant_id in joined_market_situation.merchants:
            for offer_id in joined_market_situation.merchants[self.merchant_id].keys():
                amount_sales = self.extract_sales(product_id, offer_id, joined_market_situation.sales)
                features = extract_features(offer_id, offer_list, universal_features, self.product_prices)
                if amount_sales == 0:
                    self.append_n_times(features_vector, sales_vector, features, 0, timestamp)
                else:
                    for i in range(amount_sales):
                        self.append_n_times(features_vector, sales_vector, features, 1, timestamp)

    def append_n_times(self, features_vector, sales_vector, features, sale_event: int, timestamp):
        latest_timestamp = TimestampConverter.from_string(self.timestamps[-1])
        current_timestamp = TimestampConverter.from_string(timestamp)
        minutes_diff = (latest_timestamp - current_timestamp).total_seconds() / 60
        n = 1
        if minutes_diff < 10:
            n = 3
        elif minutes_diff < 60:
            n = 2
        for _ in range(n):
            sales_vector.append(sale_event)
            features_vector.append(features)

    @staticmethod
    def create_offer_list(joined_market_situation: JoinedMarketSituation):
        offer_list = []
        for offers in joined_market_situation.merchants.values():
            offer_list.extend(offers.values())
        return offer_list

    def convert_training_data(self, universal_features=False):
        converted = dict()
        for product_id in self.joined_data.keys():
            new_training_data = self.create_training_data(product_id, universal_features)
            # check if at least one sale event is positive
            if 1 in new_training_data[1]:
                converted[product_id] = new_training_data
        return converted

    @staticmethod
    def extract_sales(product_id, offer_id, sales: List):
        if not sales:
            return 0
        return [x[1] for x in sales].count(offer_id)

    def print_info(self):
        counter_ms = 0
        counter_s = 0

        for product in self.joined_data.values():
            for situation in product.values():
                counter_s += len(situation.sales)
                for merchant in situation.merchants.values():
                    counter_ms += len(merchant)

        print('\nTraining data: \n\tEntries market_situations: {} \
               \n\tEntries sales: {} \
               \n\tDistinct timestamps: {} \
               \n\tFirst timestamp: {} \
               \n\tLast timestamp: {} \n\
               '.format(counter_ms, counter_s,
                        len(self.timestamps), self.timestamps[0], self.timestamps[-1]))

    def append_marketplace_situations(self, line, csv_merchant_id=None):
        merchant_id = line['merchant_id']
        if csv_merchant_id == merchant_id:
            merchant_id = self.merchant_id

        if len(self.timestamps) > 0 and line['timestamp'] <= self.timestamps[-1]:
            return
        self.prepare_joined_data(line['product_id'], line['timestamp'], merchant_id)
        merchant = self.joined_data[line['product_id']][line['timestamp']].merchants[merchant_id]
        if line['offer_id'] not in merchant:
            merchant[line['offer_id']] = Offer(line['amount'], line['merchant_id'], line['offer_id'], line['price'],
                                               line['prime'], line['product_id'], line['quality'],
                                               {'standard': line['shipping_time_standard'], 'prime': line['shipping_time_prime']},
                                               '', line['uid'])

    def prepare_joined_data(self, product_id: str, timestamp: str, merchant_id=None):
        if product_id not in self.joined_data:
            self.joined_data[product_id] = {}
        if timestamp not in self.joined_data[product_id]:
            self.joined_data[product_id][timestamp] = JoinedMarketSituation()
        if merchant_id and merchant_id not in self.joined_data[product_id][timestamp].merchants:
            self.joined_data[product_id][timestamp].merchants[merchant_id] = {}

    def append_sales(self, line: dict):
        if self.last_sale_timestamp and line['timestamp'] <= self.last_sale_timestamp:
            return
        index = bisect.bisect(self.timestamps, line['timestamp']) - 1
        if index < 0:
            return

        index = self.find_index_of_corresponding_market_situation(index, line['product_id'], line['offer_id'])

        self.total_sale_events += 1
        if index != -1:
            timestamp = self.timestamps[index]
            self.last_sale_timestamp = line['timestamp']

            self.prepare_joined_data(line['product_id'], timestamp)

            interval = self.joined_data[line['product_id']][timestamp]
            interval.sales.append((line['timestamp'], line['offer_id']))

            # add price to price list
            self.add_product_price(line['product_id'], line['price'])
        else:
            self.sales_wo_ms += 1
            logging.warning("Did not find a corresponding market situation for sale event! Ignore...   (" + str(self.sales_wo_ms) + "/" + str(self.total_sale_events) + ")")

    def add_product_price(self, product_id: str, price: str):
        if product_id not in self.product_prices:
            self.product_prices[product_id] = []
        self.product_prices[product_id].append(float(price))

    def find_index_of_corresponding_market_situation(self, index: int, product_id: str, offer_id: str):
        if self.test_index(index, product_id, offer_id):
            return index
        for i in range(1, 11):
            if index - 1 >= 0 and self.test_index(index - 1, product_id, offer_id):
                return index - i
            if index + i < len(self.timestamps) and self.test_index(index + 1, product_id, offer_id):
                return index + i
        return -1

    def test_index(self, index: int, product_id: str, offer_id: str):
        if product_id in self.joined_data \
                and self.timestamps[index] in self.joined_data[product_id] \
                and self.merchant_id in self.joined_data[product_id][self.timestamps[index]].merchants \
                and offer_id in self.joined_data[product_id][self.timestamps[index]].merchants[self.merchant_id]:
            return True
        else:
            return False

    def append_by_csvs(self, market_situations_path, buy_offer_path, csv_merchant_id=None):
        with open(market_situations_path, 'r') as csvfile:
            has_header = csv.Sniffer().has_header(csvfile.read(16384))
            csvfile.seek(0)
            if has_header:
                situation_data = csv.DictReader(csvfile)
            else:
                situation_data = csv.DictReader(csvfile, fieldnames=get_market_situation_fieldnames())
            for line in situation_data:
                self.append_marketplace_situations(line, csv_merchant_id)
        self.update_timestamps()
        with open(buy_offer_path, 'r') as csvfile:
            has_header = csv.Sniffer().has_header(csvfile.read(16384))
            csvfile.seek(0)
            if has_header:
                buy_offer_data = csv.DictReader(csvfile)
            else:
                buy_offer_data = csv.DictReader(csvfile, fieldnames=get_buy_offer_fieldnames())
            for line in buy_offer_data:
                self.append_sales(line)
        self.print_info()

    def append_by_kafka(self, market_situations_path=None, buy_offer_path=None):
        ########## use kafka example files
        if market_situations_path and buy_offer_path:
            self.append_by_csvs(market_situations_path, buy_offer_path)
            return
        #############

        try:
            ms, bo = download_kafka_files(self.merchant_token)

        except Exception as e:
            logging.warning('Could not download data from kafka: {}'.format(e))
            return
        if ms.status_code != 200 or bo.status_code != 200 or len(ms.text) < 10 or len(bo.text) < 10:
            logging.warning('Kafka download failed')
            return

        situation_data = csv.DictReader(ms.text.split('\n'))
        for line in situation_data:
            self.append_marketplace_situations(line)
        self.update_timestamps()
        buy_offer_data = csv.DictReader(bo.text.split('\n'))
        for line in buy_offer_data:
            self.append_sales(line)
        self.print_info()
