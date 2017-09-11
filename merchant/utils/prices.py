import random
from typing import List

from numpy import arange


class PriceUtils:
    def random_price(self, price: float):
        return round(price * random.uniform(0.8, 3), 2)

    def calculate_expected_profits(self, potential_prices: List[float], price: float, probas: List):
        return [(proba * (potential_prices[i] - price)) for i, proba in enumerate(probas)]

    def get_potential_prices(self, price, use_random_distance=False):
        if use_random_distance:
            return self.__get_potential_prices_with_random_distance(price)
        else:
            return self.__get_potential_prices_with_fixed_distance(price)

    def __get_potential_prices_with_random_distance(self, price):
        min_difference = 1  # in cent
        max_difference = 50  # in cent
        lowest_price = price * 0.9
        highest_price = price * 3

        potential_prices = list()
        price = lowest_price
        while price <= highest_price:
            potential_prices.append(price)
            price += (random.randint(min_difference, max_difference) * 0.01)
        return potential_prices

    def __get_potential_prices_with_fixed_distance(self, price):
        return list(arange(price * 0.9, price * 3, 0.05))
