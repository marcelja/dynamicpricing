from unittest import TestCase
from unittest.mock import patch

from MlMerchant import MLMerchant
from tests.helper.ml_testengine import MlTestEngine
from utils.settingsbuilder import SettingsBuilder


class TestMLMerchant(TestCase):
    @patch.multiple(MLMerchant, __abstractmethods__=set())
    def setUp(self):
        self.tested = MLMerchant(SettingsBuilder().build(), MlTestEngine())

    # Tests
    def test_get_potential_prices_without_random_distances(self):
        expected = self.create_expected_potential_prices_without_random_distances()

        actual = self.tested.get_potential_prices(10, False)

        self.assert_potential_prices_without_random_distances(actual, expected)

    def test_potential_prices_with_random_distances_are_in_range(self):
        actual = self.tested.get_potential_prices(10, True)

        self.assertGreaterEqual(len(actual), 43)
        self.assertLessEqual(len(actual), 2100)
        print("Potential Prices with random distance: ", actual)

    def test_random_price_is_in_range(self):
        actual = self.tested.random_price(10)

        self.assertGreaterEqual(actual, 8)
        self.assertLessEqual(actual, 30)

    def test_calculate_expected_profits(self):
        expected = [-0.3, -0.2, 0.0, 0.3, 0.7]

        actual = self.tested.calculate_expected_profits([9, 9.5, 10, 10.5, 11], 10.0, [0.3, 0.4, 0.5, 0.6, 0.7])

        self.assertListEqual(expected, actual)

    # Helper functions
    def assert_potential_prices_without_random_distances(self, actual, expected):
        self.assertEqual(420, len(actual))
        for i in range(len(actual)):
            self.assertAlmostEqual(expected[i], actual[i])

    def create_expected_potential_prices_without_random_distances(self):
        expected = list()
        for i in range(900, 3000, 5):
            expected.append(round((i * 0.01), 2))
        return expected

