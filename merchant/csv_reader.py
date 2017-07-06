import csv

from merchant.buy_offer import BuyOffer
from merchant.market_situation import MarketSituation
from merchant.timestamp_converter import TimestampConverter


class CSVReader:
    def __init__(self):
        self.buy_offer = []
        self.market_situation = []
        self.market_situation_at_time = {}
        self.buy_offer_at_time = {}
        self.csv_merchant_id = None
        self.newest_ms_timestamp = None
        self.newest_bo_timestamp = None

    def read_buy_offer(self):
        with open('../data/buyOffer.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                new_buy_offer = BuyOffer(row)
                self.check_and_set_merchant_id(new_buy_offer)
                self.buy_offer.append(new_buy_offer)
                self.organize_buy_offer_by_time(new_buy_offer)

    def read_market_situation(self):
        with open('../data/marketSituation.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                new_market_situation = MarketSituation(row)
                self.market_situation.append(new_market_situation)
                self.organize_market_situation_by_time(new_market_situation)

    def read_kafka_market_situation(self, new_market_situation):
        result = []
        newest_timestamp = self.newest_ms_timestamp
        for row in new_market_situation:
            timestamp = TimestampConverter.from_string(row[10])
            if self.newest_ms_timestamp is None or timestamp > self.newest_ms_timestamp:  # filter old entries
                result.append(MarketSituation(None, row))
                if newest_timestamp is None or timestamp > newest_timestamp:
                    newest_timestamp = timestamp
        self.newest_ms_timestamp = newest_timestamp
        return result

    def read_kafka_buy_offer(self, new_buy_offer):
        result = []
        newest_timestamp = self.newest_bo_timestamp
        for row in new_buy_offer:
            if row[3] != 200:  # http code
                continue
            timestamp = TimestampConverter.from_string(row[10])
            if self.newest_bo_timestamp is None or timestamp > self.newest_bo_timestamp:  # filter old entries
                result.append(BuyOffer(None, row))
                if newest_timestamp is None or timestamp > newest_timestamp:
                    newest_timestamp = timestamp
        self.newest_bo_timestamp = newest_timestamp
        return result

    def organize_market_situation_by_time(self, market_situation):
        if market_situation.timestamp_object not in self.market_situation_at_time:
            self.market_situation_at_time[market_situation.timestamp_object] = []
        self.market_situation_at_time[market_situation.timestamp_object].append(market_situation)

    def organize_buy_offer_by_time(self, buy_offer):
        if buy_offer.timestamp_object not in self.buy_offer_at_time:
            self.buy_offer_at_time[buy_offer.timestamp_object] = []
        self.buy_offer_at_time[buy_offer.timestamp_object].append(buy_offer)

    def get_buy_offer(self):
        return self.buy_offer

    def get_market_situation(self):
        return self.market_situation

    def get_buy_offer_at_time(self):
        return self.buy_offer_at_time

    def get_market_situation_at_time(self):
        return self.market_situation_at_time

    def check_and_set_merchant_id(self, new_buy_offer):
        if self.csv_merchant_id is None:
            self.csv_merchant_id = new_buy_offer.merchant_id
        elif new_buy_offer.merchant_id != self.csv_merchant_id:
            raise ValueError("Illegal State: got multiple merchant_ids in buyOffer!")
