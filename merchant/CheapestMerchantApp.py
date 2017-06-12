import argparse
import sys

sys.path.append('./')
sys.path.append('../')
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant_sdk.models import Offer

'''
    Template for Ruby deployment to insert defined tokens
'''
merchant_token = "{{API_TOKEN}}"
#merchant_token = 'fikFWZXKVZIlioyFt3e55BSPoWUArm4XVom2OKMusegbTfqNiVRngtDWQhfIUjoz'
merchant_token = "ng6OkL54Zv84WZSPWhjLD1mR4niOxJmmysBjFGnoCvsiUL823rNGsAhwwRMvj9hi"

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'initialProducts': 5,
    'shipping': 5,
    'primeShipping': 1,
    'maxReqPerSec': 40.0,
    'underprice': 0.2
    }

def get_from_list_by_key(dict_list, key, value):
    elements = [elem for elem in dict_list if elem[key] == value]
    if elements:
        return elements[0]
    return None


class MerchantSampleLogic(MerchantBaseLogic):
    def __init__(self):
        MerchantBaseLogic.__init__(self)
        global settings
        self.settings = settings

        '''
            Information store
        '''
        self.products = {}
        self.offers = {}

        '''
            Predefined API token
        '''
        self.merchant_id = settings['merchant_id']
        self.merchant_token = merchant_token

        '''
            Setup API
        '''
        PricewarsRequester.add_api_token(self.merchant_token)
        self.marketplace_api = MarketplaceApi(host=self.settings['marketplace_url'])
        self.producer_api = ProducerApi(host=self.settings['producer_url'])

        '''
            Start Logic Loop
        '''
        self.run_logic_loop()

    def update_api_endpoints(self):
        """
        Updated settings may contain new endpoints, so they need to be set in the api client as well.
        However, changing the endpoint (after simulation start) may lead to an inconsistent state
        :return: None
        """
        self.marketplace_api.host = self.settings['marketplace_url']
        self.producer_api.host = self.settings['producer_url']

    '''
        Implement Abstract methods / Interface
    '''

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        print('update settings')
        def cast_to_expected_type(key, value, def_settings=self.settings):
            if key in def_settings:
                return type(def_settings[key])(value)
            else:
                return value

        new_settings_casted = dict([
            (key, cast_to_expected_type(key, new_settings[key]))
            for key in new_settings
        ])

        self.settings.update(new_settings_casted)
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

    '''
        Merchant Logic for being the cheapest
    '''
    def setup(self):
        try:
            marketplace_offers = self.marketplace_api.get_offers()
            for i in range(settings['initialProducts']):
                self.buy_product_and_update_offer(marketplace_offers)
        except Exception as e:
            print('error on setup:', e)

    def execute_logic(self):
        try:
            offers = self.marketplace_api.get_offers()
            missing_offers = self.settings["initialProducts"] - len(self.offers)

            for product in self.products.values():
                if product.uid in self.offers:
                    offer = self.offers[product.uid]
                    offer.price = self.calculate_prices(offers, product.uid, product.price, product.product_id)
                    try:
                        self.marketplace_api.update_offer(offer)
                    except Exception as e:
                        print('error on updating an offer:', e)
                else:
                    print ('ERROR: product uid is not in offers; skipping')
        except Exception as e:
            print('error on executing the logic:', e)
        return settings['maxReqPerSec']/10

    def calculate_prices(self, marketplace_offers, product_uid, purchase_price, product_id):
        print('calc prices')
        competitive_offers = []
        [competitive_offers.append(offer) for offer in marketplace_offers if offer.merchant_id != self.merchant_id and offer.product_id == product_id]
        cheapest_offer = 999

        if len(competitive_offers) == 0:
            return 2 * purchase_price
        for offer in competitive_offers:
            if offer.price < cheapest_offer:
                cheapest_offer = offer.price

        new_price = cheapest_offer - settings['underprice']
        if new_price < purchase_price:
            new_price = purchase_price

        return new_price

    def add_new_product_to_offers(self, new_product, marketplace_offers):
        new_offer = Offer.from_product(new_product)
        new_offer.price = self.calculate_prices(marketplace_offers, new_product.uid, new_product.price, new_product.product_id)
        new_offer.shipping_time = {
            'standard': settings['shipping'],
            'prime': settings['primeShipping']
        }
        new_offer.prime = True
        try:
            new_offer.offer_id = self.marketplace_api.add_offer(new_offer).offer_id
            self.products[new_product.uid] = new_product
            self.offers[new_product.uid] = new_offer
        except Exception as e:
            print('error on adding a new offer:', e)

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

    def buy_product_and_update_offer(self, marketplace_offers):
        print('buy prod')
        try:
            new_product = self.producer_api.buy_product()

            if new_product.uid in self.products:
                self.restock_existing_product(new_product, marketplace_offers)
            else:
                self.add_new_product_to_offers(new_product, marketplace_offers)
        except Exception as e:
            print('error on buying a new product:', e)


merchant_logic  = MerchantSampleLogic()
merchant_server = MerchantServer(merchant_logic)
app = merchant_server.app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant Being Cheapest')
    parser.add_argument('--port', type=int,
                        help='port to bind flask App to')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
