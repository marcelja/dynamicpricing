from unittest import TestCase

from numpy.core.multiarray import arange

from MlMerchant import MLMerchant
from settings import Settings
from unittest.mock import patch


class TestMLMerchant(TestCase):

    @patch.multiple(MLMerchant, __abstractmethods__=set())
    def setUp(self):
        self.tested = MLMerchant(Settings.create(None))

    # Tests
    def test_get_potential_prices_without_random_distances(self):
        expected = self.create_expected_potential_prices_without_random_distances()

        actual = self.tested.get_potential_prices(10, False)

        self.assert_potential_prices_without_random_distances(actual, expected)

    def test_get_potential_prices_with_random_distances(self):
        actual = self.tested.get_potential_prices(10, True)

        self.assertGreaterEqual(len(actual), 43)
        self.assertLessEqual(len(actual), 2100)
        print("Potential Prices with random distance: ", actual)

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

