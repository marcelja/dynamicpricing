import argparse
import logging
from typing import List

from sklearn.neural_network import MLPRegressor

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings
from time import time


class MLPMerchant(MLMerchant):
    def __init__(self):
        self.universal_model = None
        super().__init__(Settings.create('mlp_models.pkl'))

    def train_model(self, features: dict):
        product_model_dict = dict()
        logging.debug('Start training')
        start_time = int(time() * 1000)
        for product_id, vector_tuple in features.items():
            # More configuration needed here
            product_model = MLPRegressor(hidden_layer_sizes=(10,),
                                         activation='relu',
                                         # def
                                         solver='adam',
                                         # learning_rate='adaptive',
                                         max_iter=1000,
                                         # learning_rate_init=0.01,
                                         verbose=True)
            # TODO: what does partial_fit() do?
            product_model.fit(vector_tuple[0], vector_tuple[1])
            product_model_dict[product_id] = product_model
        end_time = int(time() * 1000)
        logging.debug('Finished training')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return product_model_dict

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        self.universal_model = MLPRegressor(hidden_layer_sizes=(10,),
                                            activation='logistic',
                                            # def
                                            solver='adam',
                                            learning_rate='adaptive',
                                            max_iter=10000,
                                            learning_rate_init=0.01,
                                            verbose=True)
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

    def train_universal_statsmodel(self, features: dict):
        # WTF??
        pass

    def predict(self, product_id, situations):
        # TODO2: It's possible, that predict return negative possibility,
        #        that's actually not possible
        return self.model[product_id].predict(situations)

    def predict_with_universal_model(self, situations: List[List[int]]):
        return self.universal_model.predict(situations)

    def predict_with_universal_statsmodel(self, situations: List[List[int]]):
        return self.universal_model.predict(situations)

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
