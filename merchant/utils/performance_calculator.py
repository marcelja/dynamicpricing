import logging
import math
import sys
import traceback
from typing import List

import numpy

from ml_engine import MlEngine
from training_data import TrainingData
from utils.feature_extractor import extract_features

CALCULATE_PRODUCT_SPECIFIC_PERFORMANCE = False
CALCULATE_UNIVERSAL_PERFORMANCE = False
NUM_OF_UNIVERSAL_FEATURES = 5
NUM_OF_PRODUCT_SPECIFIC_FEATURES = 14


class PerformanceCalculator:
    def __init__(self, ml_engine: MlEngine, merchant_id: str):
        self.ml_engine = ml_engine
        self.merchant_id = merchant_id

    def calc_performance(self, training_data: TrainingData, merchant_id: str):
        if not CALCULATE_PRODUCT_SPECIFIC_PERFORMANCE and not CALCULATE_UNIVERSAL_PERFORMANCE:
            return
        logging.debug('Calculating performance')
        sales_probabilities_ps = []
        sales_ps = []
        probability_per_offer = []
        sales_probabilities_uni = []
        sales_uni = []

        for joined_market_situations in training_data.joined_data.values():
            for jms in joined_market_situations.values():
                if merchant_id in jms.merchants:
                    for offer_id in jms.merchants[merchant_id].keys():
                        amount_sales = TrainingData.extract_sales(jms.merchants[merchant_id][offer_id].product_id, offer_id, jms.sales)
                        if CALCULATE_PRODUCT_SPECIFIC_PERFORMANCE:
                            features_ps = extract_features(offer_id, TrainingData.create_offer_list(jms), False, training_data.product_prices)
                        if CALCULATE_UNIVERSAL_PERFORMANCE:
                            features_uni = extract_features(offer_id, TrainingData.create_offer_list(jms), True, training_data.product_prices)
                        if amount_sales == 0:
                            self.__add_product_specific_probabilities(features_ps, jms, offer_id, sales_probabilities_ps, sales_ps, 0, probability_per_offer)
                            self.__add_universal_probabilities(features_uni, sales_probabilities_uni, sales_uni, 0)
                        else:
                            for i in range(amount_sales):
                                self.__add_product_specific_probabilities(features_ps, jms, offer_id, sales_probabilities_ps, sales_ps, 1, probability_per_offer)
                                self.__add_universal_probabilities(features_uni, sales_probabilities_uni, sales_uni, 1)
        if CALCULATE_PRODUCT_SPECIFIC_PERFORMANCE:
            self.__process_performance_calculation(sales_probabilities_ps, sales_ps, NUM_OF_PRODUCT_SPECIFIC_FEATURES, "Product-specific")
        if CALCULATE_UNIVERSAL_PERFORMANCE:
            self.__process_performance_calculation(sales_probabilities_uni, sales_uni, NUM_OF_UNIVERSAL_FEATURES, "Universal")

    def __process_performance_calculation(self, sales_probabilities: List, sales: List, num_of_features: int, model_name: str):
        logging.info(model_name + " performance:")
        self.calculate_performance(sales_probabilities, sales, num_of_features)

    def __add_universal_probabilities(self, features_uni, sales_probabilities_uni, sales_uni, sale_success: int):
        if CALCULATE_UNIVERSAL_PERFORMANCE:
            sales_uni.append(sale_success)
            sales_probabilities_uni.append(self.ml_engine.predict_with_universal_model([features_uni]))

    def __add_product_specific_probabilities(self, features_ps, jms, offer_id, sales_probabilities_ps, sales_ps, sale_success: int, probability_per_offer):
        if CALCULATE_PRODUCT_SPECIFIC_PERFORMANCE:
            sales_ps.append(sale_success)
            probability = self.ml_engine.predict(jms.merchants[self.merchant_id][offer_id].product_id, [features_ps])
            sales_probabilities_ps.append(probability)

    def calculate_performance(self, sales_probabilities: List[float], sales: List[int], feature_count: int):
        try:
            ll1, ll0, aic = self.__calculate_aic(sales_probabilities, sales, feature_count)
            mcf = self.__calculate_mcfadden(ll1, ll0)
            return ll1, ll0, aic, mcf
        except ValueError:
            logging.error("Error in performance calculation!")
            traceback.print_exc(file=sys.stdout)

    def __calculate_aic(self, sales_probabilities: List[float], sales: List[int], feature_count: int):
        # sales_probabilities: [0.35, 0.29, ...]
        # sales: [0, 1, 1, 0, ...]
        # feature_count: int

        # Für jede Situation:
        # verkauft? * log(verkaufswahrsch.) + (1 - verkauft?) * (1 - log(1-verkaufswahrsch.))
        # var LL  = sum{i in 1..B} ( y[i]*log(P[i]) + (1-y[i])*log(1-P[i]) );

        # Nullmodel: Average sales probability based on actual sales
        # Some stuff to read about it:
        # https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faq-what-are-pseudo-r-squareds/
        # http://www.karteikarte.com/card/2013125/null-modell

        # http://avesbiodiv.mncn.csic.es/estadistica/ejemploaic.pdf
        # AIC = -2*ln(likelihood) + 2*K
        # with k = number of parameters in the model
        # with likelihood function from slides:
        # product of p^yi ⋅(1−p)^1−yi (probability of sale if sold, counter probability else)

        if len(sales) != 0:
            avg_sales = sum(sales) / len(sales)
        else:
            avg_sales = 0

        ll = self.__likelihood(sales, sales_probabilities)
        logging.info('Log likelihood is: {}'.format(ll))

        ll0 = self.__likelihood_nullmodel(sales, avg_sales)
        logging.info('LL0 is: {}'.format(ll0))

        aic = - 2 * ll + 2 * feature_count
        logging.info('AIC is: {}'.format(aic))

        return ll, ll0, aic

    def __likelihood(self, sales, sales_probabilities):
        ll = 0
        for i in range(len(sales)):
            ll += sales[i] * math.log(sales_probabilities[i]) + (1 - sales[i]) * (math.log(1 - sales_probabilities[i]))
        return ll

    def __log_likelihood(self, y_true, y_pred):
        ones = numpy.full(len(y_pred), 1)
        return sum(y_true * numpy.log(y_pred) + (ones - y_true) * numpy.log(ones - y_pred))

    def __likelihood_nullmodel(self, sales, average_sales):
        ll0 = 0
        for i in range(len(sales)):
            ll0 += sales[i] * math.log(average_sales) + (1 - sales[i]) * (math.log(1 - average_sales))
        return ll0

    def __calculate_mcfadden(self, ll1, ll0):
        if ll0 == 0:  # prevent division by zero
            mcf = -1
        else:
            mcf = 1 - ll1 / ll0
        logging.debug('Hint: 0.2 < mcf < 0.4 is a good fit (higher value is better)')
        logging.info('McFadden R squared is: {}'.format(mcf))
        return mcf
