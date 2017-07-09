from merchant_sdk import MerchantBaseLogic
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant_sdk.models import Offer


class SuperMerchant(MerchantBaseLogic):
    def __init__(self, settings):
        MerchantBaseLogic.__init__(self)

        self.settings = settings

        '''
            Internal state handling
        '''
        self.execQueue = []

        '''
            Information store
        '''
        self.products = {}
        self.offers = {}

        '''
            Predefined API token
        '''
        self.merchant_id = settings["merchant_id"]
        self.merchant_token = settings["merchant_token"]
        '''
            Setup API
        '''
        PricewarsRequester.add_api_token(self.merchant_token)
        self.marketplace_api = MarketplaceApi(host=self.settings["marketplace_url"])
        self.producer_api = ProducerApi(host=self.settings["producer_url"])

    def update_api_endpoints(self):
        """
        Updated settings may contain new endpoints, so they need to be set in the api client as well.
        However, changing the endpoint (after simulation start) may lead to an inconsistent state
        :return: None
        """
        self.marketplace_api.host = self.settings["marketplace_url"]
        self.producer_api.host = self.settings["producer_url"]

    '''
        Implement Abstract methods / Interface
    '''

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        MerchantBaseLogic.update_settings(self, new_settings)
        self.update_api_endpoints()
        return self.settings

    def sold_offer(self, offer):
        if self.state != 'running':
            return
        try:
            offers = self.marketplace_api.get_offers()
            self.buy_product_and_update_offer(offers)
        except Exception as e:
            print('error on handling a sold offer:', e)

    def buy_product_and_update_offer(self, marketplace_offers):
        try:
            new_product = self.producer_api.buy_product()

            if new_product.uid in self.products:
                self.restock_existing_product(new_product, marketplace_offers)
            else:
                self.add_new_product_to_offers(new_product, marketplace_offers)
        except Exception as e:
            print('error on buying a new product:', e)

    def restock_existing_product(self, new_product, marketplace_offers):
        print('restock product', new_product)
        product = self.products[new_product.uid]
        product.amount += new_product.amount
        product.signature = new_product.signature

        offer = self.offers[product.uid]
        print('in this offer:', offer)
        offer.price = self.calculate_prices(marketplace_offers, product.uid, product.price, product.product_id)
        offer.amount = product.amount
        offer.signature = product.signature
        try:
            self.marketplace_api.restock(offer.offer_id, new_product.amount, offer.signature)
        except Exception as e:
            print('error on restocking an offer:', e)

    def add_new_product_to_offers(self, new_product, marketplace_offers):
        new_offer = Offer.from_product(new_product)
        new_offer.price = self.calculate_prices(marketplace_offers, new_product.uid, new_product.price, new_product.product_id)
        new_offer.shipping_time = {
            'standard': self.settings["shipping"],
            'prime': self.settings["primeShipping"]
        }
        new_offer.prime = True
        try:
            new_offer.offer_id = self.marketplace_api.add_offer(new_offer).offer_id
            self.products[new_product.uid] = new_product
            self.offers[new_product.uid] = new_offer
        except Exception as e:
            print('error on adding a new offer:', e)
