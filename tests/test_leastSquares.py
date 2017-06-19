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
        self.assertEqual(8869, len(self.leastSquares.buy_offer))
        self.assertEqual(61243, len(self.leastSquares.market_situation_at_time))
        self.assertEqual(8869, len(self.leastSquares.buy_offer_at_time))

    def test_init_training(self):
        self.assertEqual(1, len(self.leastSquares.x_prices))
        self.assertTrue('1' in self.leastSquares.x_prices.keys())

    def test_update_training_data(self):
        self.leastSquares.update_training_data()
