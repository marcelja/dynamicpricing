from typing import List

from.PricewarsBaseApi import PricewarsBaseApi
from ..models import Offer, MerchantRegisterResponse, ApiException


class MarketplaceApi(PricewarsBaseApi):

    def __init__(self, host='http://vm-mpws2016hp1-04.eaalab.hpi.uni-potsdam.de:8080/marketplace', debug=False):
        PricewarsBaseApi.__init__(self, host=host, debug=debug)

    def get_offers(self, include_empty_offers=False) -> List[Offer]:
        params = {}
        if include_empty_offers:
            params['include_empty_offer'] = True
        r = self.request('get', 'offers', params=params)
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())
        return Offer.from_list(r.json())

    def add_offer(self, offer: Offer) -> Offer:
        r = self.request('post', 'offers', json=offer.to_dict())
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())
        return Offer.from_dict(r.json())

    def update_offer(self, offer: Offer):
        r = self.request('put', 'offers/{:d}'.format(offer.offer_id), json=offer.to_dict())
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())

    def restock(self, offer_id=-1, amount=0, signature=''):
        body = {
            'amount': amount,
            'signature': signature
        }
        r = self.request('patch', 'offers/{:d}/restock'.format(offer_id), json=body)
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())

    def register_merchant(self, api_endpoint_url='', merchant_name='', algorithm_name='') -> MerchantRegisterResponse:
        body = {
            'api_endpoint_url': api_endpoint_url,
            'merchant_name': merchant_name,
            'algorithm_name': algorithm_name
        }
        r = self.request('post', 'merchants', json=body)
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())
        return MerchantRegisterResponse.from_dict(r.json())

    def unregister_merchant(self, merchant_token=''):
        r = self.request('delete', 'merchants/{:s}'.format(merchant_token))
        if 400 <= r.status_code < 500:
            raise ApiException(r.json())
