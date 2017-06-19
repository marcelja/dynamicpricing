import unittest
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

    @unittest.skip("Requires running kafka container, only enable if docker has been started")
    def test_update_training_data(self):
        self.leastSquares.update_training_data()

    def test_find_previous_ms_returns_valid_entry(self):
        market_situation = []
        expected = {'amount': '2', 'merchant_id': 'test_merchant', 'offer_id': '1', 'price': '17.5', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                     'shipping_time_standard': '5', 'timestamp': '2017-05-29T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'}
        market_situation.append(expected)
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '1', 'price': '14.3', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-29T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '1', 'merchant_id': 'test_merchant', 'offer_id': '2', 'price': '18.6', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '2', 'price': '19.1', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        self.assertEqual(expected, self.leastSquares.find_previous_ms(market_situation, '1', 'test_merchant', '2017-05-30T06:27:02.410Z'))

    def test_find_previous_ms_returns_none(self):
        market_situation = []
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '1', 'price': '14.3', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-29T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '1', 'merchant_id': 'test_merchant', 'offer_id': '2', 'price': '18.6', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '2', 'price': '19.1', 'prime': '1', 'product_id': '1', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        self.assertEqual(None, self.leastSquares.find_previous_ms(market_situation, '1', 'test_merchant', '2017-05-30T06:27:02.410Z'))

    def test_update_training_data_from_market_situation(self):
        market_situation = []
        market_situation.append({'amount': '2', 'merchant_id': 'test_merchant', 'offer_id': '1', 'price': '17.5', 'prime': '1', 'product_id': '42', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-29T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '1', 'price': '14.3', 'prime': '1', 'product_id': '42', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-29T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '1', 'merchant_id': 'test_merchant', 'offer_id': '2', 'price': '18.6', 'prime': '1', 'product_id': '42', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})
        market_situation.append({'amount': '2', 'merchant_id': 'other', 'offer_id': '2', 'price': '19.1', 'prime': '1', 'product_id': '42', 'quality': '1', 'shipping_time_prime': '1',
                                 'shipping_time_standard': '5', 'timestamp': '2017-05-30T06:27:02.410Z', 'triggering_merchant_id': 'test_merchant'})

        self.assertEqual(1, len(self.leastSquares.x_prices))
        self.leastSquares.update_ms_training_data(market_situation)
        self.assertEqual(2, len(self.leastSquares.x_prices))
        self.assertEqual('17.5', self.leastSquares.x_prices['42'][0]['price'])
