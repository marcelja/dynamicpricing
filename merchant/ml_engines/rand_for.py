import logging
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from typing import List

from sklearn.ensemble import RandomForestRegressor

from ml_engine import MlEngine


class RandomForestEngine(MlEngine):
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
        product_model = RandomForestRegressor(n_estimators=75)
        product_model.fit(data[0], data[1])
        self.set_product_model_thread_safe(product_id, product_model)

    def predict(self, product_id: str, situations: List):
        predicted = self.product_model_dict[product_id].predict(situations)
        for idx, predict in enumerate(predicted):
            predicted[idx] = max(predicted[idx], 0.000001)
            predicted[idx] = min(predicted[idx], 0.999999)
        return predicted

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        start_time = int(time() * 1000)
        universal_model = RandomForestRegressor(n_estimators=75)
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

    def predict_with_universal_model(self, situations: List[List[int]]):
        predicted = self.universal_model.predict(situations)
        for idx, predict in enumerate(predicted):
            predicted[idx] = max(predicted[idx], 0.000001)
            predicted[idx] = min(predicted[idx], 0.999999)
        return predicted
