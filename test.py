import csv
import datetime
from collections import defaultdict

INITIAL_MARKETSITUATION_CSV_PATH = 'data/marketSituation.csv'
COMPETITOR_OFFERS = defaultdict(dict)
OWN_OFFERS = defaultdict(dict)
merchant_id = 'test'
vectors = dict()

def main():
    global merchant_id

    market_situation = []
    sales = []
    with open('data/marketSituation.csv', 'r') as csvfile:
        fieldnames = ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id', 'quality', ' shipping_time_prime', 'shipping_time_standard', 'timestamp', 'triggering_merchant_id', 'uid']
        situation_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for situation in situation_reader:
            market_situation.append(situation)

    with open('data/buyOffer.csv', 'r') as csvfile:
        fieldnames = ['amount', 'consumer_id', 'http_code', 'left_in_stock', 'merchant_id', 'offer_id', 'price', 'product_id', 'quality', 'timestamp', 'uid']
        sales_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for sale in sales_reader:
            sales.append(sale)

    merchant_id = sales[0]['merchant_id']

    timestamp = market_situation[0]['timestamp']
    current_offers = []
    sales_counter = 0

    for situation in market_situation:
        if timestamp == situation['timestamp']:
            current_offers.append(situation)
        else:
            own_sales = []
            while to_timestamp(sales[sales_counter]['timestamp']) < to_timestamp(situation['timestamp']):
                if sales[sales_counter]['http_code'][0] == '2':
                    own_sales.append(sales[sales_counter])
                sales_counter += 1

            calculate_features(current_offers, own_sales)

            timestamp = situation['timestamp']
            current_offers.clear()
            current_offers.append(situation)


def to_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


def calculate_features(offers, sales):
    global merchant_id, vectors
    for offer in offers:
        if offer['merchant_id'] == merchant_id:
            OWN_OFFERS[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])
        else:
            COMPETITOR_OFFERS[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])

    items_sold = [sold['offer_id'] for sold in sales]

    for product_id, offers in OWN_OFFERS.items():
        # Layout: Ownprice, quality, price_rank, (amount_of_offers), average_price_on_market, distance_to_cheapest, (amount_of_comp)
        features = []
        for offer_id, values in offers.items():
            own_price = float(values[0])
            features.append(own_price)
            features.append(int(values[1]))
            price_list = [float(offer[0]) for offer in COMPETITOR_OFFERS[product_id].values()]
            features.append(calculate_price_rank(price_list, own_price))
            features.append(len(COMPETITOR_OFFERS[product_id].values()))
            features.append(sum(price_list) / len(price_list))
            features.append(own_price - min(price_list))

            sold = 1 if offer_id in items_sold else 0

            if not vectors.get(product_id):
                vectors[product_id] = ([], [])
            vectors[product_id][0].append(features)
            vectors[product_id][1].append(sold)


def calculate_price_rank(price_list, own_price):
    price_rank = 1
    for price in price_list:
        if own_price > price:
            price_rank += 1
    return price_rank





if __name__ == '__main__':
    main()
