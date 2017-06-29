import sys
import logging
import os
import base64
import hashlib
import datetime
import csv
from collections import defaultdict
import requests
import math

sys.path.append('./')
sys.path.append('../')
from merchant_sdk.api import KafkaApi, PricewarsRequester


INITIAL_BUYOFFER_CSV_PATH = '../data/buyOffer.csv'
INITIAL_MARKETSITUATION_CSV_PATH = '../data/marketSituation.csv'


def learn_from_csvs(token):
    logging.debug('Reading csv files')
    market_situation = []
    sales = []
    with open(INITIAL_MARKETSITUATION_CSV_PATH, 'r') as csvfile:
        fieldnames = ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id', 'quality', ' shipping_time_prime', 'shipping_time_standard', 'timestamp', 'triggering_merchant_id', 'uid']
        situation_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for situation in situation_reader:
            market_situation.append(situation)

    with open(INITIAL_BUYOFFER_CSV_PATH, 'r') as csvfile:
        fieldnames = ['amount', 'consumer_id', 'http_code', 'left_in_stock', 'merchant_id', 'offer_id', 'price', 'product_id', 'quality', 'timestamp', 'uid']
        sales_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for sale in sales_reader:
            sales.append(sale)
    logging.debug('Finished reading of csv files')
    merchant_id = sales[0]['merchant_id']
    return aggregate(market_situation, sales, merchant_id)


def download_data_and_aggregate(merchant_token, merchant_id):
    # Dont know, if we need that URL at some point
    # 'http://vm-mpws2016hp1-05.eaalab.hpi.uni-potsdam.de:8001'
    PricewarsRequester.add_api_token(merchant_token)
    logging.debug('Downloading files from Kafka ...')
    kafka_url = os.getenv('PRICEWARS_KAFKA_REVERSE_PROXY_URL', 'http://127.0.0.1:8001')
    kafka_api = KafkaApi(host=kafka_url)
    csvs = {'marketSituation': None, 'buyOffer': None}
    topics = ['marketSituation', 'buyOffer']

    for topic in topics:
        try:
            data_url = kafka_api.request_csv_export_for_topic(topic)
            # TODO error handling for empty csvs
            resp = requests.get(data_url, timeout=2)
            print("topic is" + topic)
            resp.text
            print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
            reader = csv.DictReader(resp.text.split("\n"))
            csvs[topic] = [line for line in reader]
        except Exception as e:
            logging.warning('Could not download data for topic {} from kafka: {}'.format(topic, e))
    logging.debug('Download finished')
    if csvs[topics[0]] and csvs[topics[1]]:
        # try:
        return aggregate(csvs['marketSituation'], csvs['buyOffer'], merchant_id)
        # except Exception as e:
        #     print(csvs)
    else:
        logging.info('Received empty csv files!')
        return None


def aggregate(market_situation, sales, merchant_id):
    vectors = dict()
    logging.debug('Starting data aggregation')

    timestamp = market_situation[0]['timestamp']
    current_offers = []
    sales_counter = 0
    for situation in market_situation:
        if timestamp == situation['timestamp']:
            current_offers.append(situation)
        else:
            own_sales = []
            # import pdb; pdb.set_trace()

            while sales_counter < len(sales) and to_timestamp(sales[sales_counter]['timestamp']) < to_timestamp(situation['timestamp']):
                if sales[sales_counter]['http_code'][0] == '2':
                    own_sales.append(sales[sales_counter])
                sales_counter += 1
            vectors = calculate_features(current_offers, own_sales, merchant_id, vectors)
            timestamp = situation['timestamp']
            current_offers.clear()
            current_offers.append(situation)
    logging.debug('Finished data aggregation')
    return vectors


def calculate_features(offers, sales, merchant_id, vectors):
    competitor_offers = defaultdict(dict)
    own_offers = defaultdict(dict)
    for offer in offers:
        if offer['merchant_id'] == merchant_id:
            own_offers[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])
        else:
            competitor_offers[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])

    items_sold = [sold['offer_id'] for sold in sales]

    for product_id, offers in own_offers.items():
        # Layout: Ownprice, quality, price_rank, (amount_of_offers), average_price_on_market, distance_to_cheapest, (amount_of_comp)
        for offer_id, values in offers.items():
            features = []
            own_price = float(values[0])
            features.append(own_price)
            features.append(int(values[1]))
            price_list = [float(offer[0]) for offer in competitor_offers[product_id].values()]
            # TODO remove the shit below, when fixed
            if not price_list:
                continue
            features.append(calculate_price_rank(price_list, own_price))
            features.append(len(competitor_offers[product_id].values()))
            features.append(sum(price_list) / len(price_list))
            features.append(own_price - min(price_list))

            sold = 1 if offer_id in items_sold else 0

            if not vectors.get(product_id):
                vectors[product_id] = ([], [])
            vectors[product_id][0].append(features)
            vectors[product_id][1].append(sold)
    return vectors


def calculate_price_rank(price_list, own_price):
    price_rank = 1
    for price in price_list:
        if own_price > price:
            price_rank += 1
    return price_rank


def to_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


def calculate_min_price(offers):
    price, quality = zip(*list(offers.values()))
    return min(list(price))


def calculate_merchant_id_from_token(token):
    return base64.b64encode(hashlib.sha256(
        token.encode('utf-8')).digest()).decode('utf-8')


def extract_features_from_offer_snapshot(price, offers, merchant_id,
                                         product_id):
    # TODO refactor!

    offers = [x for x in offers if product_id == x.product_id]
    features = [price]
    own_offer = [x for x in offers if x.merchant_id == merchant_id]
    features.append(own_offer[0].quality)
    price_list = [x.price for x in offers if x.merchant_id != merchant_id]
    features.append(calculate_price_rank(price_list, price))
    features.append(len(price_list))
    # TODO remove the shit below, when fixed
    if not price_list:
        return features
    features.append(sum(price_list) / len(price_list))
    features.append(price - min(price_list))
    return features


def calculate_aic(sales_probabilities, sales, feature_count):

    # Für jede Situation:
    # verkauft? * log(verkaufswahrsch.) + (1 - verkauft?) * (1 - log(1-verkaufswahrsch.))
    # var LL  = sum{i in 1..B} ( y[i]*log(P[i]) + (1-y[i])*log(1-P[i]) );

    ll = 0

    # Nullmodell: Average sales probability based on actual sales
    # Some stuff to read about it:
    # https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-what-are-pseudo-r-squareds/
    # http://www.karteikarte.com/card/2013125/null-modell

    ll0 = 0.5

    for i in range(len(sales)):
        ll += sales[i] * math.log(sales_probabilities[i]) +\
            (1 - sales[i]) * (math.log(1 - sales_probabilities[i]))
        ll0 += sales[i]

    ll0 = ll0 / len(sales)
    aic = - 2 * ll + 2 * feature_count

    logging.info('Log likelihood is: {}'.format(ll))
    logging.info('AIC is: {}'.format(aic))

    calculate_mcfadden(ll, ll0)


def calculate_mcfadden(ll1, ll0):

    mcf = 1 - (math.log(ll1) / math.log(ll0))
    logging.debug('Hint: 0.2 < mcf < 0.4 is a good fit (higher is good)')
    logging.info('McFadden R squared is: {}'.format(mcf))
