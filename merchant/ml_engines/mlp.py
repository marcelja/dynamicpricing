import logging
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from typing import List

from sklearn.neural_network import MLPRegressor

from ml_engine import MlEngine


class MlpEngine(MlEngine):
    def train_model(self, features: dict):
        logging.debug('Start training')
        product_ids = features.keys()
        start_time = int(time() * 1000)
        with ThreadPoolExecutor(max_workers=8) as executor:
            thread_list = [executor.submit(self.train_model_for_id, product_id, features[product_id]) for product_id in product_ids]
            wait(thread_list)
        end_time = int(time() * 1000)
        logging.debug('Finished training')
        logging.debug('Training took {} ms'.format(end_time - start_time))

    def train_model_for_id(self, product_id, data):
        product_model = MLPRegressor(hidden_layer_sizes=(5,),
                                     activation='relu',
                                     solver='adam',
                                     learning_rate='adaptive',
                                     max_iter=1000,
                                     learning_rate_init=0.01,
                                     alpha=0.01)
        product_model.fit(data[0], data[1])
        self.set_product_model_thread_safe(product_id, product_model)

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        universal_model = MLPRegressor(hidden_layer_sizes=(5,),
                                       activation='relu',
                                       solver='adam',
                                       learning_rate='adaptive',
                                       max_iter=1000,
                                       learning_rate_init=0.01,
                                       alpha=0.01)
        start_time = int(time() * 1000)
        f_vector = []
        s_vector = []
        for product_id, vector_tuple in features.items():
            f_vector.extend(vector_tuple[0])
            s_vector.extend(vector_tuple[1])
        universal_model.fit(f_vector, s_vector)
        end_time = int(time() * 1000)
        logging.debug('Finished training universal model')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        self.set_universal_model_thread_safe(universal_model)

    def predict(self, product_id, situations):
        predicted = self.product_model_dict[product_id].predict(situations)
        return [max(0.000001, min(predict, 0.999999)) for predict in predicted]

    def predict_with_universal_model(self, situations: List[List[int]]):
        predicted = self.universal_model.predict(situations)
        return [max(0.000001, min(predict, 0.999999)) for predict in predicted]
