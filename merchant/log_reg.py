from MlMerchant import MLMerchant
from merchant_sdk import MerchantBaseLogic, MerchantServer
import os
import logging
import argparse
from sklearn.linear_model import LogisticRegression

if os.getenv('API_TOKEN'):
    merchant_token = os.getenv('API_TOKEN')
else:
    merchant_token = '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl'
initial_merchant_id = 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM='

settings = {
    'merchant_id': MerchantBaseLogic.calculate_id(merchant_token),
    'marketplace_url': MerchantBaseLogic.get_marketplace_url(),
    'producer_url': MerchantBaseLogic.get_producer_url(),
    'kafka_reverse_proxy_url': MerchantBaseLogic.get_kafka_reverse_proxy_url(),
    'debug': True,
    'max_amount_of_offers': 10,
    'shipping': 2,
    'primeShipping': 1,
    'max_req_per_sec': 10.0,
    'learning_interval': 2.0,
    'data_file': 'log_reg_models.pkl'
}


class LogisticRegressionMerchant(MLMerchant):
    def __init__(self):
        self.model = dict()
        super().__init__(merchant_token, settings)

    def train_model(self, features):
        # TODO include time and amount of sold items to featurelist
        logging.debug('Start training')
        for product_id, vector_tuple in features.items():
            product_model = LogisticRegression()
            product_model.fit(vector_tuple[0], vector_tuple[1])
            self.model[product_id] = product_model
        logging.debug('Finished training')

    def predict(self, product_id, situations):
        # TODO: What happens if there is no such product_id ?
        return self.model[product_id].predict_proba(situations)[:, 1]

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
