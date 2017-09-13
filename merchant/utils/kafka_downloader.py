import logging
import os

import requests

from merchant_sdk.api import PricewarsRequester, KafkaApi


def download_kafka_files(merchant_token, kafka_url):
    logging.debug('Downloading files from Kafka ...')
    PricewarsRequester.add_api_token(merchant_token)
    kafka_api = KafkaApi(host=kafka_url)
    data_url_ms = kafka_api.request_csv_export_for_topic('marketSituation')
    data_url_bo = kafka_api.request_csv_export_for_topic('buyOffer')
    return requests.get(data_url_ms, timeout=2), requests.get(data_url_bo, timeout=2)
