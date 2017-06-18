import argparse
import sys
import os

sys.path.append('./')
sys.path.append('../')
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant_sdk.models import Offer
from SuperMerchant import SuperMerchant

# not sure, whether this token stuff brakes something

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '2ZnJAUNCcv8l2ILULiCwANo7LGEsHCRJlFdvj18MvG8yYTTtCfqN3fTOuhGCthWf'

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


class RuleBasedMerchant(SuperMerchant):

    def __init__(self):
        super().__init__(merchant_token, settings)
        self.run_logic_loop()


# This method might be moved to super, maybe
    def setup(self):
        try:
            marketplace_offers = self.marketplace_api.get_offers()
            for i in range(self.settings['initialProducts']):
                self.buy_product_and_update_offer(marketplace_offers)
        except Exception as e:
            print('error on setup:', e)

    def execute_logic(self):
        try:
            offers = self.marketplace_api.get_offers()
            # What does this thing do? Was in sample code
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
            print('error on executing lloolloollthe logic:', e)
        return settings['maxReqPerSec'] / 10

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant Being Cheapest')
    parser.add_argument('--port', type=int,
                        help='port to bind flask App to')
    args = parser.parse_args()
    server = MerchantServer(RuleBasedMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
