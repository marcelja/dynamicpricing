import logging
import os

import dill as pickle
import pandas as pd

from merchant_sdk.api import KafkaApi, PricewarsRequester

NUM_OF_UNIVERSAL_FEATURES = 5
NUM_OF_PRODUCT_SPECIFIC_FEATURES = 14


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


def load_history(file):
    with open(file, 'rb') as m:
        return pickle.load(m)


def save_training_data(data, file):
    with open(file, 'wb') as m:
        pickle.dump(data, m)


def write_calculations_to_file(probability_per_offer, file_path):
    with open(file_path, 'w') as output:
        output.write(str(probability_per_offer))

def get_buy_offer_fieldnames():
    return ['amount','consumer_id','http_code','left_in_stock','merchant_id',
        'offer_id','price','product_id','quality','timestamp','uid']

def get_market_situation_fieldnames():
    return ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id',
        'quality', 'shipping_time_prime', 'shipping_time_standard', 'timestamp',
        'triggering_merchant_id', 'uid']
