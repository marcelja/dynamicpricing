from unittest import TestCase

from utils.settingsbuilder import SettingsBuilder


class TestSettings(TestCase):
    # Tests
    def test_initialize(self):
        expected = self.get_expected_default_settings()

        actual = SettingsBuilder().build()

        self.assertDictEqual(expected, actual)

    def test_with_data_file(self):
        expected = self.get_expected_settings_with_data_file()

        actual = SettingsBuilder().with_data_file("some_file.txt").build()

        self.assertDictEqual(expected, actual)

    def test_with_initial_learning_parameters(self):
        expected = self.get_expected_settings_with_initial_learning_parameters()
        ilp = self.get_initial_learning_parameters_to_test()

        actual = SettingsBuilder().with_initial_learning_parameters(ilp).build()

        self.assertDictEqual(expected, actual)

    def test_with_merchant_token(self):
        expected = self.get_expected_settings_with_merchant_token()

        actual = SettingsBuilder().with_merchant_token("any_token").build()

        self.assertDictEqual(expected, actual)

    # Helper functions
    def get_expected_default_settings(self):
        return {
            "merchant_token": '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl',
            "merchant_id": 'ckDTybPfqJtzpeRpRs1FGbuTPZlJa6vlFpCsJPAI2Oo=',
            "marketplace_url": 'http://127.0.0.1:8080',
            "producer_url": 'http://127.0.0.1:3050',
            "kafka_reverse_proxy_url": 'http://127.0.0.1:8001',
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            "data_file": None,
            "underprice": 0.2,
            "initialProducts": 5,
            "market_situation_csv_path": '../data/marketSituation.csv',
            "buy_offer_csv_path": '../data/buyOffer.csv',
            "initial_merchant_id": 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=',
            "testing_set_csv_path": '../data/marketSituation.csv',
            "output_file": '../tmp/out.txt'
        }

    def get_expected_settings_with_data_file(self):
        return {
            "merchant_token": '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl',
            "merchant_id": 'ckDTybPfqJtzpeRpRs1FGbuTPZlJa6vlFpCsJPAI2Oo=',
            "marketplace_url": 'http://127.0.0.1:8080',
            "producer_url": 'http://127.0.0.1:3050',
            "kafka_reverse_proxy_url": 'http://127.0.0.1:8001',
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            "data_file": '../tmp/some_file.txt',
            "underprice": 0.2,
            "initialProducts": 5,
            "market_situation_csv_path": '../data/marketSituation.csv',
            "buy_offer_csv_path": '../data/buyOffer.csv',
            "initial_merchant_id": 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=',
            "testing_set_csv_path": '../data/marketSituation.csv',
            "output_file": '../tmp/out.txt'
        }

    def get_expected_settings_with_initial_learning_parameters(self):
        return {
            "merchant_token": '0hjzYcmGQUKnCjtHKki3UN2BvMJouLBu2utbWgqwBBkNuefFOOJslK4hgOWbihWl',
            "merchant_id": 'ckDTybPfqJtzpeRpRs1FGbuTPZlJa6vlFpCsJPAI2Oo=',
            "marketplace_url": 'http://127.0.0.1:8080',
            "producer_url": 'http://127.0.0.1:3050',
            "kafka_reverse_proxy_url": 'http://127.0.0.1:8001',
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            "data_file": None,
            "underprice": 0.2,
            "initialProducts": 5,
            "market_situation_csv_path": 'testValue1',
            "buy_offer_csv_path": 'testValue2',
            "initial_merchant_id": 'testValue3',
            "testing_set_csv_path": 'testValue4',
            "output_file": 'testValue5'
        }

    def get_initial_learning_parameters_to_test(self):
        return {
            'train': "testValue1",
            'buy': "testValue2",
            'merchant_id': "testValue3",
            'testing_set': "testValue4",
            'output_file': "testValue5"
        }

    def get_expected_settings_with_merchant_token(self):
        return {
            "merchant_token": 'any_token',
            "merchant_id": 'kGVmtzxiGd9wjcHFp6Jvn98/qHqtnrZBpvD2At0CtaY=',
            "marketplace_url": 'http://127.0.0.1:8080',
            "producer_url": 'http://127.0.0.1:3050',
            "kafka_reverse_proxy_url": 'http://127.0.0.1:8001',
            "debug": True,
            "max_amount_of_offers": 10,
            "shipping": 2,
            "primeShipping": 1,
            "max_req_per_sec": 10.0,
            "learning_interval": 2.0,
            "data_file": None,
            "underprice": 0.2,
            "initialProducts": 5,
            "market_situation_csv_path": '../data/marketSituation.csv',
            "buy_offer_csv_path": '../data/buyOffer.csv',
            "initial_merchant_id": 'DaywOe3qbtT3C8wBBSV+zBOH55DVz40L6PH1/1p9xCM=',
            "testing_set_csv_path": '../data/marketSituation.csv',
            "output_file": '../tmp/out.txt'
        }
