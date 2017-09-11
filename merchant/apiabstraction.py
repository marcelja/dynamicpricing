from abc import ABC, abstractmethod
from typing import List

from merchant_sdk.models import Offer, MerchantRegisterResponse, Product


class ApiAbstraction(ABC):
    @abstractmethod
    def get_offers(self, include_empty_offers=False) -> List[Offer]:
        pass

    @abstractmethod
    def add_offer(self, offer: Offer) -> Offer:
        pass

    @abstractmethod
    def update_offer(self, offer: Offer):
        pass

    @abstractmethod
    def restock(self, offer_id=-1, amount=0, signature=''):
        pass

    @abstractmethod
    def register_merchant(self, api_endpoint_url='', merchant_name='', algorithm_name='') -> MerchantRegisterResponse:
        pass

    @abstractmethod
    def unregister_merchant(self, merchant_token=''):
        pass

    @abstractmethod
    def buy_product(self) -> Product:
        pass

    @abstractmethod
    def get_products(self) -> List[Product]:
        pass

    @abstractmethod
    def add_products(self, products: List[Product]):
        pass

    @abstractmethod
    def update_products(self, products: List[Product]):
        pass

    @abstractmethod
    def get_product(self, product_uid) -> Product:
        pass

    @abstractmethod
    def add_product(self, product: Product):
        pass

    @abstractmethod
    def update_product(self, product: Product):
        pass

    @abstractmethod
    def delete_product(self, product_uid):
        pass

    @abstractmethod
    def update_marketplace_url(self, marketplace_url: str):
        pass

    @abstractmethod
    def update_producer_url(self, producer_url: str):
        pass
