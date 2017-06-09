import sys
import merchant_sdk
from merchant_sdk.api import MarketplaceApi, ProducerApi, PricewarsRequester

MERCHANT_TOKEN = 'Fjndoqs0Ie14rPY9g994bDUwoIOEyRq6LMBrhMFNV69='

marketplace_endpoint = 'http://localhost:8080'
marketplace_api = MarketplaceApi(host=marketplace_endpoint)

producer_endpoint = 'http://localhost:3050'
producer_api = ProducerApi(host=producer_endpoint)

# Register merchant in the management UI. Or run following:
# marketplace_api.register_merchant(api_endpoint_url='http://localhost:5000/',
#                                   merchant_name='test_merchant',
#                                   algorithm_name='test123')

PricewarsRequester.add_api_token(MERCHANT_TOKEN)
