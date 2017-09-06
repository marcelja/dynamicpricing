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
    def __init__(self, initial_learning_parameters=None):
        self.product_model_dict = dict()
        self.universal_model = None
        settings = Settings.create('log_reg_models.pkl',
                                   initial_learning_parameters=initial_learning_parameters)
        super().__init__(settings)

    def train_model(self, features: dict):
        # TODO include time and amount of sold items to featurelist
        start_time = int(time() * 1000)
        logging.debug('Start training')
        product_ids = features.keys()
        with ThreadPoolExecutor(max_workers=8) as executor:
            thread_list = [executor.submit(self.train_model_for_id, product_id, features[product_id]) for product_id in product_ids]
            wait(thread_list)
        end_time = int(time() * 1000)
        [print(product_model.coef_) for product_model in self.product_model_dict.values()]
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
        description='PriceWars Merchant doing Logistic Regression',
        formatter_class=argparse.MetavarTypeHelpFormatter)
    parser.add_argument('--port',
                        type=int,
                        default=5101,
                        help='Port to bind flask App to, default is 5101')
    parser.add_argument('--train',
                        type=str,
                        help='Path to csv file for training')
    parser.add_argument('--buy',
                        type=str,
                        help='Path to buyOffer.csv')
    parser.add_argument('--merchant',
                        type=str,
                        help='Merchant ID for initial csv parsing')
    parser.add_argument('--test',
                        type=str,
                        help='Path to csv file for cross validation')
    parser.add_argument('--output',
                        type=str,
                        help='Output will be written into the spedified file')
    args = parser.parse_args()
    if args.train and args.buy and args.merchant and args.test and args.output:
        initial_learning_parameters = {}
        initial_learning_parameters['train'] = args.train
        initial_learning_parameters['buy'] = args.buy
        initial_learning_parameters['merchant_id'] = args.merchant
        initial_learning_parameters['testing_set'] = args.test
        initial_learning_parameters['output_file'] = args.output
        logging.info('Using given settings for cross validation...')
        LogisticRegressionMerchant(initial_learning_parameters).cross_validation()
    else:
        logging.info('Not enough parameters for cross validation specified!')
        logging.info('Starting server')
        server = MerchantServer(LogisticRegressionMerchant())
        app = server.app
        app.run(host='0.0.0.0', port=args.port)
