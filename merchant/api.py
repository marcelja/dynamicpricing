from typing import List

from apiabstraction import ApiAbstraction
from merchant_sdk.api import MarketplaceApi, ProducerApi, PricewarsRequester
from merchant_sdk.models import Offer, MerchantRegisterResponse, Product


class Api(ApiAbstraction):

    def __init__(self, merchant_token, marketplace_url, producer_url):
        PricewarsRequester.add_api_token(merchant_token)
        self.marketplace_api = MarketplaceApi(host=marketplace_url)
        self.producer_api = ProducerApi(host=producer_url)

    def add_offer(self, offer: Offer) -> Offer:
        return self.marketplace_api.add_offer(offer)

    def unregister_merchant(self, merchant_token=''):
        return self.marketplace_api.unregister_merchant(merchant_token)

    def register_merchant(self, api_endpoint_url='', merchant_name='', algorithm_name='') -> MerchantRegisterResponse:
        return self.marketplace_api.register_merchant(api_endpoint_url, merchant_name, algorithm_name)

    def update_offer(self, offer: Offer):
        return self.update_offer(offer)

    def get_offers(self, include_empty_offers=False) -> List[Offer]:
        return self.marketplace_api.get_offers(include_empty_offers)

    def restock(self, offer_id=-1, amount=0, signature=''):
        return self.marketplace_api.restock(offer_id, amount, signature)

    def add_product(self, product: Product):
        return self.producer_api.add_product(product)

    def get_product(self, product_uid) -> Product:
        return self.producer_api.get_product(product_uid)

    def add_products(self, products: List[Product]):
        return self.producer_api.add_products(products)

    def update_product(self, product: Product):
        return self.producer_api.update_product(product)

    def update_products(self, products: List[Product]):
        return self.producer_api.update_products(products)

    def delete_product(self, product_uid):
        return self.producer_api.delete_product(product_uid)

    def get_products(self) -> List[Product]:
        return self.producer_api.get_products()

    def buy_product(self) -> Product:
        return self.producer_api.buy_product()

    def update_marketplace_url(self, marketplace_url: str):
        self.marketplace_api.host = marketplace_url

    def update_producer_url(self, producer_url: str):
        self.producer_api.host = producer_url
