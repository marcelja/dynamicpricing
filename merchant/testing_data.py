import csv
from merchant_sdk.models import Offer
from models.joined_market_situation import JoinedMarketSituation
from collections import defaultdict


class TestingData(object):
    def __init__(self):
        self.joined_data = {}
        self.timestamps = []
        # Note: Can't store all prizes from sales, since we have no sales, do we?
        self.product_price_list = defaultdict(list)
        self.product_prices = {product_id: sum(price_list) / len(price_list)
                               for product_id, price_list in self.product_price_list.items()}

    def append_by_csvs(self, market_situations_path, csv_merchant_id):
        with open(market_situations_path, 'r') as csvfile:
            situation_data = csv.DictReader(csvfile)
            for line in situation_data:
                self.append_marketplace_situations(line, csv_merchant_id)

    def append_marketplace_situations(self, line, csv_merchant_id):
        self.prepare_joined_data(line['product_id'], line['timestamp'], csv_merchant_id)
        self.product_price_list[line['product_id']].append(line['price'])
        merchant = self.joined_data[line['product_id']][line['timestamp']].merchants[csv_merchant_id]
        if line['offer_id'] not in merchant:
            merchant[line['offer_id']] = Offer(line['amount'], line['merchant_id'], line['offer_id'], line['price'],
                                               line['prime'], line['product_id'], line['quality'],
                                               {'standard': line['shipping_time_standard'], 'prime': line['shipping_time_prime']},
                                               '', line['uid'])

    def prepare_joined_data(self, product_id: str, timestamp: str, merchant_id):
        if product_id not in self.joined_data:
            self.joined_data[product_id] = dict()
        if timestamp not in self.joined_data[product_id]:
            self.joined_data[product_id][timestamp] = JoinedMarketSituation()
        if merchant_id and merchant_id not in self.joined_data[product_id][timestamp].merchants:
            self.joined_data[product_id][timestamp].merchants[merchant_id] = {}
