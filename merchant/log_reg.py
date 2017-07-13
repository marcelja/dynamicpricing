import argparse
import logging
from typing import List

from sklearn.linear_model import LogisticRegression
from sklearn.utils import shuffle

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings


class LogisticRegressionMerchant(MLMerchant):
    def __init__(self):
        self.model = dict()
        self.universal_model: LogisticRegression = None
        super().__init__(Settings.create('log_reg_models.pkl'))

    def train_model(self, features: dict):
        # TODO include time and amount of sold items to featurelist
        logging.debug('Start training')
        for product_id, vector_tuple in features.items():
            product_model = LogisticRegression()
            f, s = shuffle(vector_tuple[0], vector_tuple[1])
            product_model.fit(f, s)
            self.model[product_id] = product_model
        logging.debug('Finished training')

    def train_universal_model(self, features: dict):
        logging.debug('Start training universal model')
        self.universal_model = LogisticRegression()
        f_vector = []
        s_vector = []
        for product_id, vector_tuple in features.items():
            f_vector.extend(vector_tuple[0])
            s_vector.extend(vector_tuple[1])
        f, s = shuffle(f_vector, s_vector)
        self.universal_model.fit(f, s)
        logging.debug('Finished training universal model')

    def predict(self, product_id: str, situations: List[List[int]]):
        # TODO: What happens if there is no such product_id ?
        return self.model[product_id].predict_proba(situations)[:, 1]

    def predict_with_universal_model(self, situations: List[List[int]]):
        return self.universal_model.predict_proba(situations)[:, 1]


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
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
