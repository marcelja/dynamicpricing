from unittest import TestCase

from merchant.least_squares import LeastSquares


class TestLeastSquares(TestCase):
    def setUp(self):
        self.leastSquares = LeastSquares()

    def test_calculate_prices(self):
        new_price = self.leastSquares.calculate_prices(None, 1, '1')
        self.assertEqual(17, int(new_price))

    def test_read_csv_file(self):
        # self.leastSquares.read_csv_file()
        self.assertEqual(411940, len(self.leastSquares.market_situation))

    def test_init_training(self):
        self.assertEqual(1, len(self.leastSquares.example_x))
        self.assertTrue('1' in self.leastSquares.example_x.keys())

