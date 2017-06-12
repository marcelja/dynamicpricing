import csv
import datetime
import numpy as np
from sklearn import linear_model
import pickle
import os

# Any1 has prime, all same prodid, shipping_time_prime,shipping_time_standard

PICKLE_FILE = 'vectors.obj'


def read_files():
    market_situations = []
    sales = []
    with open('marketSituation.csv', 'r') as csvfile:
        fieldnames = ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id', 'quality', ' shipping_time_prime', 'shipping_time_standard', 'timestamp', 'triggering_merchant_id', 'uid']
        situation_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for situation in situation_reader:
            market_situations.append(situation)

    with open('buyOffer.csv', 'r') as csvfile:
        fieldnames = ['amount', 'consumer_id', 'http_code', 'left_in_stock', 'merchant_id', 'offer_id', 'price', 'product_id', 'quality', 'timestamp', 'uid']
        sales_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for sale in sales_reader:
            sales.append(sale)
    return market_situations, sales


def join(market_situations, sales):

    # Layout: [price (float), pricerank1 (int), quality (int)]
    eventvector = []
    sale_events = []
    offers = dict()
    own_merchant_id = sales[0]['merchant_id']

    sales_counter = 0
    price_rank = 0
    quality = 0
    price = -1

    for idx, situation in enumerate(market_situations):
        timestamp_market = to_timestamp(situation['timestamp'])

        offers[situation['offer_id']] = (float(situation['price']), int(situation['quality']))

        # We updated our own price
        if situation['merchant_id'] == own_merchant_id:
            price = float(situation['price'])
            price_rank = calculate_price_rank(offers, price)
            quality = int(situation['quality'])

        # Calculate sales events for situation
        if len(market_situations) > idx + 1 and \
            sales_counter <= len(sales) and \
                to_timestamp(market_situations[idx + 1]['timestamp']) > to_timestamp(sales[sales_counter]['timestamp']):

            sales_current_situation = 0
            while to_timestamp(sales[sales_counter]['timestamp']) < timestamp_market:
                sales_counter += 1
                # TODO: do something with amount of sold items
                sales_current_situation += 1
                eventvector.append([float(price), price_rank, quality])
                sale_events.append(1)
        else:
            sale_events.append(0)
            eventvector.append([float(price), price_rank, quality])

    assert len(eventvector) == len(sale_events)

    # Serialize objects for reuse
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump((eventvector, sale_events), f)

    demand_learning(eventvector, sale_events)


def demand_learning(situation, sold):
    reg = linear_model.LogisticRegression(fit_intercept=False)
    x = np.asarray(situation, dtype=np.int64)
    y = np.asarray(sold, dtype=np.int64)

    reg.fit(x, y)

    predictions = reg.predict_proba([[20, 1, 1], [50, 7, 1]])
    print(predictions)


def to_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


def calculate_price_rank(offers, own_price):
    price_rank = 1
    for price, quality in list(offers.values()):
        if own_price > float(price):
            price_rank += 1
    return price_rank

if __name__ == '__main__':

    if os.path.isfile(PICKLE_FILE):
        with open(PICKLE_FILE, 'rb') as f:
            vectors = pickle.load(f)
        demand_learning(vectors[0], vectors[1])
    else:
        situations, sales = read_files()
        join(situations, sales)

