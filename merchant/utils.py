import sys
import pandas as pd
import logging

sys.path.append('./')
sys.path.append('../')
from merchant_sdk.api import KafkaApi, PricewarsRequester
import os
import base64
import hashlib
import sys
import numpy as np
import datetime
import csv
from collections import defaultdict


INITIAL_BUYOFFER_CSV_PATH = '../data/buyOffer.csv'
INITIAL_MARKETSITUATION_CSV_PATH = '../data/marketSituation.csv'


COMPETITOR_OFFERS = defaultdict(dict)
OWN_OFFERS = defaultdict(dict)
vectors = dict()


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


    for topic in ['marketSituation', 'buyOffer']:
        try:
            data_url = kafka_api.request_csv_export_for_topic(topic)
            # TODO do we really need panda? Isnt the standard csv reader sufficient?
            csvs[topic] = pd.read_csv(data_url)
        except pd.io.common.EmptyDataError as e:
            logging.warning('Kafka returned an empty csv for topic {}'.format(topic))
        except Exception as e:
            logging.warning('Could not download data for topic {} from kafka: {}'.format(topic, e))
    logging.debug('Download finished')
    joined = aggregate(csvs['marketSituation'].to_records(), csvs['buyOffer'].to_records(), merchant_id)
    return joined


def aggregate(market_situation, sales, merchant_id):
    global vectors
    logging.debug('Starting data aggregation')
    import pdb; pdb.set_trace()
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
            calculate_features(current_offers, own_sales, merchant_id)

            timestamp = situation['timestamp']
            current_offers.clear()
            current_offers.append(situation)
    logging.debug('Finished data aggregation')
    return vectors


def calculate_features(offers, sales, merchant_id):
    global vectors
    for offer in offers:
        if offer['merchant_id'] == merchant_id:
            OWN_OFFERS[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])
        else:
            COMPETITOR_OFFERS[offer['product_id']][offer['offer_id']] = (offer['price'], offer['quality'])

    items_sold = [sold['offer_id'] for sold in sales]

    for product_id, offers in OWN_OFFERS.items():
        # Layout: Ownprice, quality, price_rank, (amount_of_offers), average_price_on_market, distance_to_cheapest, (amount_of_comp)
        for offer_id, values in offers.items():
            features = []
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


def to_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


def calculate_min_price(offers):
    price, quality = zip(*list(offers.values()))
    return min(list(price))



# def aggregate(csvs, token):
    # Method stole from eyample MLmerchant
    """
    aggregate is going to transform the downloaded two csv it into a suitable data format, based on:
        $timestamp_1, $merchant_id_1, $product_id, $quality, $price
        $timestamp_1, $product_id, $sku, $price

        $timestamp_1, $sold_yes_no, $own_price, $own_price_rank, $cheapest_competitor, $best_competitor_quality
    :return:
    """

    # joined_situations = dict()
    # situation = csvs['marketSituation']
    # sales = csvs['buyOffer']

    # # If csvs are empty
    # if situation.empty and sales.empty:
    #     return joined_situations

    # own_sales = sales[sales['http_code'] == 200].copy()
    # own_sales.loc[:, 'timestamp'] = match_timestamps(situation['timestamp'], own_sales['timestamp'])
    # merchant_id = calculate_merchant_id_from_token(token)

    # logging.debug('Aggregating data')

    # for product_id in np.unique(situation['product_id']):
    #     ms_df_prod = situation[situation['product_id'] == product_id]

    #     dict_array = []
    #     for timestamp, group in ms_df_prod.groupby('timestamp'):
    #         features = extract_features_from_offer_snapshot(group, merchant_id)
    #         features.update({
    #             'timestamp': timestamp,
    #             'sold': own_sales[own_sales['timestamp'] == timestamp]['amount'].sum(),
    #         })
    #         dict_array.append(features)

    #     joined_situations[product_id] = dict_array
    # logging.debug('Finished data aggregation')
    # return joined_situations


def calculate_merchant_id_from_token(token):
    return base64.b64encode(hashlib.sha256(
        token.encode('utf-8')).digest()).decode('utf-8')


# def match_timestamps(continuous_timestamps, point_timestamps):
#     # WHAT ???
#     t_ms = pd.DataFrame({
#         'timestamp': continuous_timestamps,
#         'origin': np.zeros((len(continuous_timestamps)))
#     })
#     t_bo = pd.DataFrame({
#         'timestamp': point_timestamps,
#         'origin': np.ones((len(point_timestamps)))
#     })

#     t_combined = pd.concat([t_ms, t_bo], axis=0).sort_values(by='timestamp')
#     original_locs = t_combined['origin'] == 1

#     t_combined.loc[original_locs, 'timestamp'] = np.nan
#     # pad: propagates last marketSituation timestamp to all following (NaN) buyOffers
#     t_padded = t_combined.fillna(method='pad')

#     return t_padded[original_locs]['timestamp']


def extract_features_from_offer_snapshot(price, offers, merchant_id,
                                         product_id):
    offers = [x for x in offers if product_id == x.product_id]
    features = [price]
    own_offer = [x for x in offers if x.merchant_id == merchant_id]
    features.append(own_offer[0].quality)
    price_list = [x.price for x in offers if x.merchant_id != merchant_id]
    features.append(calculate_price_rank(price_list, price))
    features.append(len(price_list))
    features.append(sum(price_list) / len(price_list))
    features.append(price - min(price_list))
    return features

#     if product_id:
#         offers_df = offers_df[offers_df['product_id'] == product_id]
#     competitors = offers_df[offers_df['merchant_id'] != merchant_id]
#     own_situation = offers_df[offers_df['merchant_id'] == merchant_id]
#     has_offer = len(own_situation) > 0
#     has_competitors = len(competitors) > 0

#     if has_offer:
#         own_offer = own_situation.sort_values(by='price').iloc[0]
#         own_price = own_offer['price']
#         own_quality = own_offer['quality']
#         price_rank = 1 + (offers_df['price'] < own_price).sum() + ((offers_df['price'] == own_price).sum()/2)
#         distance_to_cheapest_competitor = float(own_price - competitors['price'].min()) if has_competitors else np.nan
#         quality_rank = (offers_df['quality'] < own_quality).sum() + 1
#         return {
#             'own_price': own_price,
#             'price_rank': price_rank,
#             'distance_to_cheapest_competitor': distance_to_cheapest_competitor,
#             'quality_rank': quality_rank,
#             'amount_of_all_competitors': amount_of_all_competitors,
#             'average_price_on_market': average_price_on_market
#         }
#     else:
#         return None
#     #     own_price = np.nan
#     #     price_rank = np.nan
#     #     distance_to_cheapest_competitor = np.nan
#     #     quality_rank = np.nan

#     amount_of_all_competitors = len(competitors)
#     average_price_on_market = offers_df['price'].mean()
