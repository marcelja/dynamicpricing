from unittest import TestCase

from performance_calculator import PerformanceCalculator
from tests.helper.ml_testengine import MlTestEngine


class TestPerformanceCalculator(TestCase):
    def setUp(self):
        self.tested = PerformanceCalculator(MlTestEngine(), 'any_merchant_id')

    # TODO: use test to validate performance calculations (these values are just copied from the output and have not been verified yet)
    def test_calculate_performance(self):
        expected_ll1 = -1.4064970684374103
        expected_ll0 = -1.9095425048844383
        expected_aic = 12.81299413687482
        expected_mcf = 0.26343767429124143

        ll1, ll0, aic, mcf = self.tested.calculate_performance([0.3, 0.5, 0.7], [0, 0, 1], 5)

        self.assertAlmostEqual(expected_ll1, ll1)
        self.assertAlmostEqual(expected_ll0, ll0)
        self.assertAlmostEqual(expected_aic, aic)
        self.assertAlmostEqual(expected_mcf, mcf)
