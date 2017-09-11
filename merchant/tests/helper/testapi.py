from typing import List

from apiabstraction import ApiAbstraction
from merchant_sdk.models import Product, Offer, MerchantRegisterResponse


# TODO: may not meet all requirements for tests yet
class TestApi(ApiAbstraction):

    def __init__(self):
        self.products = dict()
        self.offers = dict()
        self.product_to_buy = None

    def set_product(self, product_id, product: Product):
        self.products[product_id] = product

    def get_product(self, product_uid) -> Product:
        return self.products[product_uid]

    def add_products(self, products: List[Product]):
        for product in products:
            self.products[product.product_id] = product

    def add_offer(self, offer: Offer) -> Offer:
        self.offers[offer.offer_id] = offer
        return offer

    def update_products(self, products: List[Product]):
        for product in products:
            self.products[product.product_id] = product

    def unregister_merchant(self, merchant_token=''):
        pass

    def register_merchant(self, api_endpoint_url='', merchant_name='', algorithm_name='') -> MerchantRegisterResponse:
        return MerchantRegisterResponse()

    def update_offer(self, offer: Offer):
        self.offers[offer.offer_id] = offer

    def get_products(self) -> List[Product]:
        return list(self.products.values())

    def restock(self, offer_id=-1, amount=0, signature=''):
        pass

    def add_product(self, product: Product):
        self.products[product.product_id] = product

    def update_product(self, product: Product):
        self.products[product.product_id] = product

    def delete_product(self, product_uid):
        if product_uid in self.products:
            del self.products[product_uid]

    def get_offers(self, include_empty_offers=False) -> List[Offer]:
        return list(self.offers.values())

    def set_product_to_buy(self, product_to_buy: Product):
        self.product_to_buy = product_to_buy

    def buy_product(self) -> Product:
        return self.product_to_buy

    def update_marketplace_url(self, marketplace_url: str):
        pass

    def update_producer_url(self, producer_url: str):
        pass
