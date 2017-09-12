from typing import List
from unittest import TestCase

from MlMerchant import MLMerchant
from merchant_sdk.models import Product, Offer
from tests.helper.ml_testengine import MlTestEngine
from tests.helper.testapi import TestApi
from training_data import TrainingData
from utils.settingsbuilder import SettingsBuilder


class TestMLMerchant(TestCase):
    def setUp(self):
        self.test_api = TestApi()
        self.ml_testengine = MlTestEngine()
        self.tested = MLMerchant(SettingsBuilder().build(), self.ml_testengine, self.test_api)

    # Tests
    def test_get_product_prices(self):
        self.test_api.products = self.create_product_list()
        expected = self.get_expected_price_dict()

        actual = self.tested.get_product_prices()

        self.assertDictEqual(expected, actual)

    def test_highest_profit_from_ml(self):
        self.arrange()
        current_offers = self.create_current_offers()
        own_offer = self.create_own_offer()
        expected = 29.95

        actual = self.tested.highest_profit_from_ml(current_offers, own_offer, 10.0)

        self.assertAlmostEqual(expected, actual)

    # Helper functions
    def create_product_list(self):
        product_list = list()
        product_list.append(Product(uid='1', price=10.0))
        product_list.append(Product(uid='2', price=20.0))
        product_list.append(Product(uid='3', price=30.0))
        return product_list

    def get_expected_price_dict(self):
        expected = dict()
        expected['1'] = 10.0
        expected['2'] = 20.0
        expected['3'] = 30.0
        return expected

    def create_current_offers(self) -> List[Offer]:
        offer_list = list()
        offer_list.append(Offer(price=20.0))
        offer_list.append(Offer(price=40.0))
        return offer_list

    def create_own_offer(self) -> Offer:
        return Offer(product_id='1', price=30.0)

    def arrange(self):
        self.ml_testengine.product_model_dict['1'] = ''
        training_data = TrainingData('', '')
        training_data.product_prices = {'1': 10.0}
        self.tested.training_data = training_data
