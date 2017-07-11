import argparse
import logging

from sklearn.ensemble import RandomForestRegressor

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from settings import Settings
from time import time


class RandomForestMerchant(MLMerchant):
    def __init__(self):
        super().__init__(Settings.create('rand_for_models.pkl'))

    def train_model(self, features):
        product_model_dict = dict()
        # TODO include time and amount of sold items to featurelist
        logging.debug('Start training')
        start_time = int(time() * 1000)
        for product_id, vector_tuple in features.items():
            # I'm puttin n_estimators in constructor,
            # since this is a good point for improvement (btw. 10 is actually default)
            product_model = RandomForestRegressor(n_estimators=10)
            product_model.fit(vector_tuple[0], vector_tuple[1])
            product_model_dict[product_id] = product_model
        end_time = int(time() * 1000)
        logging.debug('Finished training')
        logging.debug('Training took {} ms'.format(end_time - start_time))
        return product_model_dict

    def predict(self, product_id, situations):
        # TODO: What happens if there is no such product_id ?
        return self.model[product_id].predict(situations)


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
