import sys

import merchant_sdk

from merchant_sdk.api import MarketplaceApi, ProducerApi, PricewarsRequester
marketplace_endpoint = 'http://localhost:8080'
marketplace_api = MarketplaceApi(host=marketplace_endpoint)

producer_endpoint = 'http://localhost:3050'
producer_api = ProducerApi(host=producer_endpoint)
