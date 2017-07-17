import argparse
import sys

sys.path.append('./')
sys.path.append('../')
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant_sdk.models import Offer
import os

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '6wrZVoz3CTUBEioPcL2lTc3d84WuCwfItXrPMrSYLwjZfYyIu24Oe71lCYgOVMfP'

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'max_amount_of_offers': 5,
    'shipping': 5,
    'primeShipping': 1,
    'max_req_per_sec': 10.0,
    'underprice': 0.2
}


class MerchantSampleLogic(MerchantBaseLogic):
    def __init__(self):
        MerchantBaseLogic.__init__(self)
        global settings
        self.settings = settings

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

    def update_settings(self, new_settings):
        MerchantBaseLogic.update_settings(self, new_settings)
        self.update_api_endpoints()
        return self.settings

    def sold_offer(self, offer):
        print('sold offer:', offer)

    '''
        Merchant Logic
    '''

    def calculate_prices(self, marketplace_offers, product_uid, purchase_price, product_id):
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

    def execute_logic(self):
        try:
            offers = self.marketplace_api.get_offers(include_empty_offers=True)
        except Exception as e:
            print('error on getting offers from the marketplace:', e)
            return 1.0 / settings['max_req_per_sec']
        own_offers = [offer for offer in offers if offer.merchant_id == self.merchant_id]
        own_offers_by_uid = {offer.uid: offer for offer in own_offers}
        missing_offers = settings['max_amount_of_offers'] - sum(offer.amount for offer in own_offers)

        new_products = []
        for _ in range(missing_offers):
            try:
                prod = self.producer_api.buy_product()
                new_products.append(prod)
            except:
                pass

        for product in new_products:
            try:
                if product.uid in own_offers_by_uid:
                    offer = own_offers_by_uid[product.uid]
                    offer.amount += product.amount
                    offer.signature = product.signature
                    self.marketplace_api.restock(offer.offer_id, amount=product.amount, signature=product.signature)
                    offer.price = self.price_product(product)
                    self.marketplace_api.update_offer(offer)
                else:
                    offer = Offer.from_product(product)
                    offer.price = self.calculate_prices(offers, product.uid, product.price, product.product_id)
                    offer.prime = True
                    offer.shipping_time['standard'] = self.settings['shipping']
                    offer.shipping_time['prime'] = self.settings['primeShipping']
                    self.marketplace_api.add_offer(offer)
            except Exception as e:
                print('could not handle product:', product, e)

        return 1.0 / settings['max_req_per_sec']


merchant_logic = MerchantSampleLogic()
merchant_server = MerchantServer(merchant_logic)
app = merchant_server.app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant cheapest')
    parser.add_argument('--port',
                        type=int,
                        default=5200,
                        help='port to bind flask App to')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
