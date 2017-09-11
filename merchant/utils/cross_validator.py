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

    def cross_validation(self):
        logging.debug('Creating testing set')
        testing_data = TestingData()
        testing_data.append_by_csvs(self.settings['testing_set_csv_path'],
                                    self.settings['initial_merchant_id'])
        logging.debug('Calculate probabilties per offer and write them to disk')
        self.calculate_sales_probality_per_offer(testing_data)

    def calculate_sales_probality_per_offer(self, testing_data: TestingData):
        probability_per_offer = []

        for joined_market_situations in testing_data.joined_data.values():
            for jms in joined_market_situations.values():
                if self.settings["initial_merchant_id"] in jms.merchants:
                    for offer_id in jms.merchants[self.settings["initial_merchant_id"]].keys():
                        features_ps = extract_features(offer_id, TrainingData.create_offer_list(jms), False, testing_data.product_prices)
                        probability = self.ml_engine.predict(jms.merchants[self.settings["initial_merchant_id"]][offer_id].product_id, [features_ps])
                        probability_per_offer.append((int(offer_id), probability[0]))
        write_calculations_to_file(probability_per_offer, self.settings['output_file'])
