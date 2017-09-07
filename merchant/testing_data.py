import csv
from merchant_sdk.models import Offer
from models.joined_market_situation import JoinedMarketSituation
from collections import defaultdict
from utils import get_market_situation_fieldnames


class TestingData(object):
    def __init__(self):
        self.joined_data = defaultdict(lambda : defaultdict(JoinedMarketSituation))
        self.timestamps = []
        # Note: Can't store all prizes from sales, since we have no sales, do we?
        self.product_prices = defaultdict(list)

    def append_by_csvs(self, market_situations_path, csv_merchant_id):
        with open(market_situations_path, 'r') as csvfile:
            has_header = csv.Sniffer().has_header(csvfile.read(16384))
            csvfile.seek(0)
            if has_header:
                situation_data = csv.DictReader(csvfile)
            else:
                situation_data = csv.DictReader(csvfile, fieldnames=get_market_situation_fieldnames())
            for line in situation_data:
                self.append_marketplace_situations(line, csv_merchant_id)

    def append_marketplace_situations(self, line, csv_merchant_id):
        self.prepare_joined_data(line['product_id'], line['timestamp'], line['merchant_id'])
        self.product_prices[line['product_id']].append(float(line['price']))

        merchant = self.joined_data[line['product_id']][line['timestamp']].merchants[line['merchant_id']]
        if line['offer_id'] not in merchant:
            merchant[line['offer_id']] = Offer(line['amount'], line['merchant_id'], line['offer_id'], line['price'],
                                               line['prime'], line['product_id'], line['quality'],
                                               {'standard': line['shipping_time_standard'], 'prime': line['shipping_time_prime']},
                                               '', line['uid'])

    def prepare_joined_data(self, product_id, timestamp, merchant_id):
        if merchant_id not in self.joined_data[product_id][timestamp].merchants:
            self.joined_data[product_id][timestamp].merchants[merchant_id] = {}
