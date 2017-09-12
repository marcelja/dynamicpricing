from unittest import TestCase

from merchant_sdk.models import Offer
from utils import feature_extractor


# TODO: extend tests
class TestExtractFeatures(TestCase):
    # Tests
    def test_extract_universal_features(self):
        expected = [1, 1, 0, 0, 0]

        actual = feature_extractor.extract_features('1', self.generate_offer_list(), True, {'1': 10.0})

        self.assertListEqual(expected, actual)

    def test_extract_product_specific_features(self):
        expected = [1, 1, 0, 0, 0, 0.0, 0, 3, 0, 0.0, 0, 0, 0, 0]

        actual = feature_extractor.extract_features('1', self.generate_offer_list(), False, {'1': 10.0})

        self.assertListEqual(expected, actual)

    # Helper functions
    def generate_offer_list(self):
        offer_list = list()
        offer_list.append(Offer(offer_id='1'))
        return offer_list
