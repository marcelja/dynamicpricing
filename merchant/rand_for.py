import argparse
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, wait

from sklearn.ensemble import RandomForestRegressor

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings
from time import time


class RandomForestMerchant(MLMerchant):
    def __init__(self):
        self.product_model_dict = dict()
        self.universal_model = None
        super().__init__(Settings.create('rand_for_models.pkl'))

    def train_model(self, features: dict):
        # TODO include time and amount of sold items to featurelist
        logging.debug('Start training')
        product_ids = features.keys()
        start_time = int(time() * 1000)
        with ThreadPoolExecutor(max_workers=8) as executor:
            thread_list = [executor.submit(self.train_model_for_id, product_id, features[product_id]) for product_id in product_ids]
            wait(thread_list)
        end_time = int(time() * 1000)
        logging.debug('Finished training')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return self.product_model_dict

    def predict(self, product_id, situations):
        # TODO: What happens if there is no such product_id ?
        return self.model[product_id].predict(situations)

    def train_model_for_id(self, product_id, data):
        product_model = RandomForestRegressor(n_estimators=100)
        product_model.fit(data[0], data[1])
        # print(product_model.coef_)
        self.product_model_dict[product_id] = product_model

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        universal_model = RandomForestRegressor(n_estimators=100)
        f_vector = []
        s_vector = []
        for product_id, vector_tuple in features.items():
            f_vector.extend(vector_tuple[0])
            s_vector.extend(vector_tuple[1])
        universal_model.fit(f_vector, s_vector)
        logging.debug('Finished training universal model')
        return universal_model

    def train_universal_statsmodel(self, features: dict):
        pass

    def predict_with_universal_model(self, situations: List[List[int]]):
        return self.universal_model.predict(situations)

    def predict_with_universal_statsmodel(self, situations: List[List[int]]):
        return self.universal_model.predict(situations)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(
        description='PriceWars Merchant doing Random Forest Regression')
    parser.add_argument('--port',
                        type=int,
                        default=5102,
                        help='Port to bind flask App to, default is 5102')
    args = parser.parse_args()
    server = MerchantServer(RandomForestMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
