import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from typing import List

from sklearn.linear_model import LogisticRegression
from sklearn.utils import shuffle

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings


class LogisticRegressionMerchant(MLMerchant):
    def __init__(self):
        self.product_model_dict = dict()
        self.universal_model = None
        super().__init__(Settings.create('log_reg_models.pkl'))

    def train_model(self, features: dict):
        # TODO include time and amount of sold items to featurelist
        start_time = int(time() * 1000)
        logging.debug('Start training')
        product_ids = features.keys()
        with ThreadPoolExecutor(max_workers=8) as executor:
            thread_list = [executor.submit(self.train_model_for_id, product_id, features[product_id]) for product_id in product_ids]
            wait(thread_list)
        end_time = int(time() * 1000)
        logging.debug('Finished training')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return self.product_model_dict

    def train_model_for_id(self, product_id, data):
        product_model = LogisticRegression(n_jobs=-1)
        product_model.fit(data[0], data[1])
        # print(product_model.coef_)
        self.product_model_dict[product_id] = product_model

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        universal_model = LogisticRegression(n_jobs=-1)
        f_vector = []
        s_vector = []
        start_time = int(time() * 1000)
        for product_id, vector_tuple in features.items():
            f_vector.extend(vector_tuple[0])
            s_vector.extend(vector_tuple[1])
        f, s = shuffle(f_vector, s_vector)
        universal_model.fit(f, s)
        end_time = int(time() * 1000)
        logging.debug('Finished training universal model')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return universal_model

    def predict(self, product_id: str, situations: List[List[int]]):
        return self.model[product_id].predict_proba(situations)[:, 1]

    def predict_with_universal_model(self, situations: List[List[int]]):
        return self.universal_model.predict_proba(situations)[:, 1]


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description='PriceWars Merchant doing Logistic Regression')
    parser.add_argument('--port',
                        type=int,
                        default=5101,
                        help='Port to bind flask App to, default is 5101')
    args = parser.parse_args()
    server = MerchantServer(LogisticRegressionMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
