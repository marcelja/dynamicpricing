import os

from merchant_sdk import MerchantBaseLogic


class SettingsBuilder:
    def __init__(self):
        self.settings = dict()
        self.initialize()

    def initialize(self):
        merchant_token = self.get_merchant_token()
        self.settings["merchant_token"] = merchant_token
        self.settings["merchant_id"] = MerchantBaseLogic.calculate_id(merchant_token)
        self.settings["marketplace_url"] = MerchantBaseLogic.get_marketplace_url()
        self.settings["producer_url"] = MerchantBaseLogic.get_producer_url()
        self.settings["kafka_reverse_proxy_url"] = MerchantBaseLogic.get_kafka_reverse_proxy_url()
        self.settings["debug"] = True
        self.settings["max_amount_of_offers"] = 10
        self.settings["shipping"] = 2
        self.settings["primeShipping"] = 1
        self.settings["max_req_per_sec"] = 10.0
        self.settings["learning_interval"] = 2.0
        self.settings["data_file"] = None
        self.settings["underprice"] = 0.2
        self.settings["initialProducts"] = 5
        self.settings["market_situation_csv_path"] = '../data/marketSituation.csv'
        self.settings["buy_offer_csv_path"] = '../data/buyOffer.csv'
        self.settings["initial_merchant_id"] = 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM='
        # TODO: create a csv for cross-validation
        self.settings["testing_set_csv_path"] = '../data/marketSituation.csv'
        self.settings["output_file"] = '../tmp/out.txt'
        return self

    def get_merchant_token(self):
        if os.getenv('API_TOKEN'):
            return os.getenv('API_TOKEN')
        else:
            # TODO: remove for Abgabe?
            return '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl'

    def with_data_file(self, data_file: str):
        if data_file is not None:
            self.settings["data_file"] = '../tmp/' + data_file
        return self

    def with_initial_learning_parameters(self, initial_learning_parameters: dict):
        if initial_learning_parameters is not None:
            self.settings["market_situation_csv_path"] = initial_learning_parameters['train']
            self.settings["buy_offer_csv_path"] = initial_learning_parameters['buy']
            self.settings["initial_merchant_id"] = initial_learning_parameters['merchant_id']
            self.settings["testing_set_csv_path"] = initial_learning_parameters['testing_set']
            self.settings["output_file"] = initial_learning_parameters['output_file']
        return self

    def with_merchant_token(self, merchant_token: str):
        if merchant_token is not None:
            self.settings["merchant_token"] = merchant_token
            self.settings["merchant_id"] = MerchantBaseLogic.calculate_id(merchant_token)
        return self

    def build(self):
        return self.settings
