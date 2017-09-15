import argparse
import random
import sys

from SuperMerchant import SuperMerchant
from apiabstraction import ApiAbstraction
from merchant_sdk import MerchantServer
from utils.settingsbuilder import SettingsBuilder

sys.path.append('./')
sys.path.append('../')


class RandomMerchant(SuperMerchant):
    def __init__(self, api: ApiAbstraction = None):
        settings = SettingsBuilder() \
            .with_merchant_token('7xCvFloHDuwm9iHDVYpjjoVzlXue01I7yU3EGsVTnSGwAXAg6yQqnvpZTkEUlWbk') \
            .build()
        settings["shipping"] = 5
        settings["max_req_per_sec"] = 40.0
        super().__init__(settings, api)
        self.run_logic_loop()

    # This method might be moved to super, maybe
    def setup(self):
        try:
            marketplace_offers = self.api.get_offers()
            for i in range(self.settings['initialProducts']):
                self.buy_product_and_update_offer(marketplace_offers)
        except Exception as e:
            print('error on setup:', e)

    def execute_logic(self):
        try:
            offers = self.api.get_offers()
            # What does this thing do? Was in sample code
            missing_offers = self.settings["initialProducts"] - len(self.offers)

            for product in self.products.values():
                if product.uid in self.offers:
                    offer = self.offers[product.uid]
                    offer.price = self.calculate_prices(offers, product.uid, product.price, product.product_id)
                    try:
                        self.api.update_offer(offer)
                    except Exception as e:
                        print('error on updating an offer:', e)
                else:
                    print('ERROR: product uid is not in offers; skipping')
        except Exception as e:
            print('error on executing lloolloollthe logic:', e)
        return self.settings['maxReqPerSec'] / 10

    def calculate_prices(self, marketplace_offers, product_uid, purchase_price, product_id):
        price = random.randint(purchase_price * 100, 10000) / 100
        print("price is: {}".format(price))
        return price


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant Being Random')
    parser.add_argument('--port', type=int, default=5104,
                        help='port to bind flask App to')
    args = parser.parse_args()
    server = MerchantServer(RandomMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
