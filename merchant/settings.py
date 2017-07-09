import os

from merchant_sdk import MerchantBaseLogic


class Settings:
    @staticmethod
    def create(data_file: str, merchant_token: str = '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl'):
        if os.getenv('API_TOKEN'):
            merchant_token = os.getenv('API_TOKEN')
        return {
            "merchant_token": merchant_token,
            "merchant_id": MerchantBaseLogic.calculate_id(merchant_token),
            "initial_merchant_id": 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=',
            "marketplace_url": MerchantBaseLogic.get_marketplace_url(),
            "producer_url": MerchantBaseLogic.get_producer_url(),
            "kafka_reverse_proxy_url": MerchantBaseLogic.get_kafka_reverse_proxy_url(),
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            "data_file": ('../tmp/' + data_file) if data_file is not None else None,
            "underprice": 0.2,
            "initialProducts": 5
        }
