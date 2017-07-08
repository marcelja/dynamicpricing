import logging
import os

import requests

from merchant_sdk.api import PricewarsRequester, KafkaApi


def download_kafka_files(merchant_token):
    logging.debug('Downloading files from Kafka ...')
    PricewarsRequester.add_api_token(merchant_token)
    kafka_url = os.getenv('PRICEWARS_KAFKA_REVERSE_PROXY_URL', 'http://127.0.0.1:8001')
    kafka_api = KafkaApi(host=kafka_url)
    data_url_ms = kafka_api.request_csv_export_for_topic('marketSituation')
    data_url_bo = kafka_api.request_csv_export_for_topic('buyOffer')
    return requests.get(data_url_ms, timeout=2), requests.get(data_url_bo, timeout=2)
