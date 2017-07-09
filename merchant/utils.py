import base64
import hashlib
import logging
import math
import os
import pickle
from typing import List

import pandas as pd

from merchant_sdk.api import KafkaApi, PricewarsRequester
from merchant_sdk.models import Offer


# TODO: adapt to new downloading process
def download_data(merchant_token):
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
            return None
        except Exception as e:
            logging.warning('Could not download data for topic {} from kafka: {}'.format(topic, e))
            return None
    logging.debug('Download finished')
    return csvs


def calculate_price_rank(price_list, own_price):
    price_rank = 1
    for price in price_list:
        if own_price > price:
            price_rank += 1
    return price_rank


def calculate_min_price(offers):
    price, quality = zip(*list(offers.values()))
    return min(list(price))


def calculate_merchant_id_from_token(token):
    return base64.b64encode(hashlib.sha256(
        token.encode('utf-8')).digest()).decode('utf-8')


def calculate_performance(sales_probabilities, sales, feature_count):
    ll1, ll0 = calculate_aic(sales_probabilities, sales, feature_count)
    calculate_mcfadden(ll1, ll0)
    precision_recall(sales_probabilities, sales)


def calculate_aic(sales_probabilities, sales, feature_count):
    # Für jede Situation:
    # verkauft? * log(verkaufswahrsch.) + (1 - verkauft?) * (1 - log(1-verkaufswahrsch.))
    # var LL  = sum{i in 1..B} ( y[i]*log(P[i]) + (1-y[i])*log(1-P[i]) );

    ll = 0

    # Nullmodel: Average sales probability based on actual sales
    # Some stuff to read about it:
    # https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-what-are-pseudo-r-squareds/
    # http://www.karteikarte.com/card/2013125/null-modell

    ll0 = 0

    average_sales = sum(sales) / len(sales)

    for i in range(len(sales)):
        ll += sales[i] * math.log(sales_probabilities[i]) + \
              (1 - sales[i]) * (math.log(1 - sales_probabilities[i]))
        ll0 += sales[i] * math.log(average_sales) + \
               (1 - sales[i]) * (math.log(1 - average_sales))

    aic = - 2 * ll + 2 * feature_count

    logging.info('Log likelihood is: {}'.format(ll))
    logging.info('LL0 is: {}'.format(ll0))
    logging.info('AIC is: {}'.format(aic))

    return ll, ll0


def calculate_mcfadden(ll1, ll0):
    mcf = 1 - ll1 / ll0
    logging.debug('Hint: 0.2 < mcf < 0.4 is a good fit (higher is good)')
    logging.info('McFadden R squared is: {}'.format(mcf))


def precision_recall(sales_probabilities, sales):
    tp = 0
    fp = 0
    fn = 0

    av = sum(sales_probabilities) / len(sales_probabilities)

    for i in range(len(sales)):
        if sales_probabilities[i] > av:
            if sales[i] == 1:
                tp += 1
            else:
                fp += 1
        elif sales[i] == 0:
            fn += 1

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    logging.warning('######### Precision/Recall might be wrong #########')
    logging.info('Precision is: {}'.format(precision))
    logging.info('Recall is: {}'.format(recall))


def extract_features(offer_id: str, offer_list: List[Offer]):
    current_offer = [x for x in offer_list if offer_id == x.offer_id][0]
    other_offers = [x for x in offer_list if offer_id != x.offer_id]
    rank = 1
    for oo in other_offers:
        if oo.price < current_offer.price:
            rank += 1
    return [rank]


def load_history(file):
    with open(file, 'rb') as m:
        return pickle.load(m)


def save_training_data(data, file):
    with open(file, 'wb') as m:
        pickle.dump(data, m)
