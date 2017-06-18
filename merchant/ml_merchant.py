from SuperMerchant import SuperMerchant
import os
from merchant_sdk import MerchantBaseLogic, MerchantServer
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi
from merchant_sdk.models import Offer
import argparse
import pickle
from utils import download_data_and_aggregate
from sklearn.linear_model import LogisticRegression


MODELS_FILE = 'models.pkl'

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '2ZnJAUNCcv8l2ILULiCwANo7LGEsHCRJlFdvj18MvG8yYTTtCfqN3fTOuhGCthWf'

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'kafka_reverse_proxy_url': MerchantBaseLogic.get_kafka_reverse_proxy_url(),
    'debug': True,
    'max_amount_of_offers': 10,
    'shipping': 5,
    'primeShipping': 1,
    'max_req_per_sec': 10.0,
    'minutes_between_learnings': 3.0,
}


def load_history():
    # Next line can be removed, when csv learning is implemented
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE, 'r') as m:
            models = pickle.load(m)
    else:
        models = dict()
    return models


def save_features(features_per_situation):
    # This might not work so far
    with open(MODELS_FILE, 'a') as m:
        pickle.dump(features_per_situation, m)


class MLMerchant(SuperMerchant):
    def __init__(self):
        super().__init__(merchant_token, settings)

        # self.models_per_product = self.load_models_from_filesystem()
        # self.last_learning = datetime.datetime.now()
        # trigger_learning(self.merchant_token, settings['kafka_reverse_proxy_url'])
        self.run_logic_loop()

    def machine_learning(self):
        history = load_history()
        features_per_situation = download_data_and_aggregate(merchant_token)
        history.update(features_per_situation)
        save_features(features_per_situation)
        models = self.train_model(features_per_situation)
        return models

    def train_model(features):
        # TODO include time and amount of sold items to featurelist
        model_products = dict()
        for product_id in features:
            data = features[product_id].dropna()
            X = data[['amount_of_all_competitors',
                      'average_price_on_market',
                      'distance_to_cheapest_competitor',
                      'price_rank',
                      'quality_rank',
                      ]]
            y = data['sold'].copy()
            y[y > 1] = 1

            model = LogisticRegression()
            model.fit(X, y)

            model_products[product_id] = model
        return model_products

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PriceWars Merchant doing fancy ML')
    parser.add_argument('--port',
                        type=int,
                        default=5100,
                        help='Port to bind flask App to, default is 5100')
    args = parser.parse_args()
    server = MerchantServer(MLMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
