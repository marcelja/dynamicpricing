import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from typing import List

from sklearn.neural_network import MLPRegressor

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings


class MLPMerchant(MLMerchant):
    def __init__(self):
        self.product_model_dict = dict()
        self.universal_model = None
        super().__init__(Settings.create('mlp_models.pkl'))
        super().initialize()

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

    def train_model_for_id(self, product_id, data):
        product_model = MLPRegressor(hidden_layer_sizes=(80,),
                                     activation='relu',
                                     solver='adam',
                                     learning_rate='adaptive',
                                     max_iter=500,
                                     learning_rate_init=0.01,
                                     alpha=0.01)
        product_model.fit(data[0], data[1])
        # print(product_model.coef_)
        self.product_model_dict[product_id] = product_model

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        self.universal_model = MLPRegressor(hidden_layer_sizes=(80,),
                                            activation='relu',
                                            solver='adam',
                                            learning_rate='adaptive',
                                            max_iter=500,
                                            learning_rate_init=0.01,
                                            alpha=0.01)
        start_time = int(time() * 1000)
        f_vector = []
        s_vector = []
        for product_id, vector_tuple in features.items():
            f_vector.extend(vector_tuple[0])
            s_vector.extend(vector_tuple[1])
        self.universal_model.fit(f_vector, s_vector)
        end_time = int(time() * 1000)
        logging.debug('Finished training universal model')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return self.universal_model

    def predict(self, product_id, situations):
        predicted = self.model[product_id].predict(situations)
        for idx, predict in enumerate(predicted):
            predicted[idx] = max(predicted[idx], 0.000001)
        return predicted

    def predict_with_universal_model(self, situations: List[List[int]]):
        predicted = self.universal_model.predict(situations)
        for idx, predict in enumerate(predicted):
            predicted[idx] = max(predicted[idx], 0.000001)
        return predicted

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description='PriceWars Merchant doing MLP Regression')
    parser.add_argument('--port',
                        type=int,
                        default=5103,
                        help='Port to bind flask App to, default is 5103')
    args = parser.parse_args()
    server = MerchantServer(MLPMerchant())
    app = server.app
    app.run(host='0.0.0.0', port=args.port)
