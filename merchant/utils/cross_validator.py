import logging

from ml_engine import MlEngine
from testing_data import TestingData
from training_data import TrainingData
from utils.feature_extractor import extract_features
from utils.utils import write_calculations_to_file


class CrossValidator:
    def __init__(self, settings: dict, ml_engine: MlEngine):
        self.settings = settings
        self.ml_engine = ml_engine
        self.testing_data = TestingData()
        self.training_data = TrainingData(self.settings['merchant_token'], self.settings['merchant_id'])

    def cross_validation(self):
        logging.debug('Creating training set')
        self.create_training_data()
        logging.debug('Creating testing set')
        self.create_testing_data()
        logging.debug('Perform learning')
        self.perform_learning()
        logging.debug('Calculate probabilties per offer and write them to disk')
        self.calculate_sales_probality_per_offer()
        logging.debug('Finished!')

    def create_training_data(self):
        self.training_data.append_by_csvs(self.settings['market_situation_csv_path'],
                                          self.settings['buy_offer_csv_path'],
                                          self.settings["initial_merchant_id"])

    def create_testing_data(self):
        self.testing_data.append_by_csvs(self.settings['testing_set_csv_path'],
                                         self.settings['initial_merchant_id'])

    def perform_learning(self):
        self.ml_engine.train_model(self.training_data.convert_training_data())

    def calculate_sales_probality_per_offer(self):
        probability_per_offer = []

        for joined_market_situations in self.testing_data.joined_data.values():
            for jms in joined_market_situations.values():
                if self.settings["initial_merchant_id"] in jms.merchants:
                    for offer_id in jms.merchants[self.settings["initial_merchant_id"]].keys():
                        features_ps = extract_features(offer_id, TrainingData.create_offer_list(jms), False, self.testing_data.product_prices)
                        probability = self.ml_engine.predict(jms.merchants[self.settings["initial_merchant_id"]][offer_id].product_id, [features_ps])
                        probability_per_offer.append((int(offer_id), probability[0]))
        write_calculations_to_file(probability_per_offer, self.settings['output_file'])
