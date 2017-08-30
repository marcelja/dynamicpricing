import os

from merchant_sdk import MerchantBaseLogic


class Settings:
    @staticmethod
    def create(data_file: str,
                # TODO: remove for Abgabe?
               merchant_token: str = '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl',
               initial_learning_parameters: dict = None):
        if os.getenv('API_TOKEN'):
            merchant_token = os.getenv('API_TOKEN')
        settings = {
            "merchant_token": merchant_token,
            "merchant_id": MerchantBaseLogic.calculate_id(merchant_token),
            "marketplace_url": MerchantBaseLogic.get_marketplace_url(),
            "producer_url": MerchantBaseLogic.get_producer_url(),
            "kafka_reverse_proxy_url": MerchantBaseLogic.get_kafka_reverse_proxy_url(),
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            # TODO: do weed need that?
            "data_file": ('../tmp/' + data_file) if data_file else None,
            "underprice": 0.2,
            "initialProducts": 5,
        }

        return Settings.set_initial_learning_parameters(settings)

    @staticmethod
    def set_initial_learning_parameters(settings, initial_learning_parameters=None):
        if initial_learning_parameters:
            settings["market_situation_csv_path"] = initial_learning_parameters['train']
            settings["buy_offer_csv_path"] = initial_learning_parameters['buy']
            settings["initial_merchant_id"] = initial_learning_parameters['merchant_id']
            settings["testing_set_csv_path"] = initial_learning_parameters['testing_set']
            settings["output_file"] = initial_learning_parameters['output_file']
        else:
            settings["market_situation_csv_path"] = '../data/marketSituation.csv'
            settings["buy_offer_csv_path"] = '../data/buyOffer.csv'
            settings["initial_merchant_id"] = 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM='
            # TODO: create a csv for cross-validation
            settings["testing_set_csv_path"] = '../data/marketSituation.csv'
            settings["output_file"] = '../tmp/mlp_out.txt'
        return settings
