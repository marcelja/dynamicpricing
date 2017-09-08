import logging
import math
import sys
import traceback
from typing import List

import numpy


def calculate_performance(sales_probabilities: List[float], sales: List[int], feature_count: int):
    try:
        ll1, ll0, aic = __calculate_aic(sales_probabilities, sales, feature_count)
        mcf = __calculate_mcfadden(ll1, ll0)
        return ll1, ll0, aic, mcf
    except ValueError:
        logging.error("Error in performance calculation!")
        traceback.print_exc(file=sys.stdout)


def __calculate_aic(sales_probabilities: List[float], sales: List[int], feature_count: int):
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

    ll = __likelihood(sales, sales_probabilities)
    logging.info('Log likelihood is: {}'.format(ll))

    ll0 = __likelihood_nullmodel(sales, avg_sales)
    logging.info('LL0 is: {}'.format(ll0))

    aic = - 2 * ll + 2 * feature_count
    logging.info('AIC is: {}'.format(aic))

    return ll, ll0, aic


def __likelihood(sales, sales_probabilities):
    ll = 0
    for i in range(len(sales)):
        ll += sales[i] * math.log(sales_probabilities[i]) + (1 - sales[i]) * (math.log(1 - sales_probabilities[i]))
    return ll


def __log_likelihood(y_true, y_pred):
    ones = numpy.full(len(y_pred), 1)
    return sum(y_true * numpy.log(y_pred) + (ones - y_true) * numpy.log(ones - y_pred))


def __likelihood_nullmodel(sales, average_sales):
    ll0 = 0
    for i in range(len(sales)):
        ll0 += sales[i] * math.log(average_sales) + (1 - sales[i]) * (math.log(1 - average_sales))
    return ll0


def __calculate_mcfadden(ll1, ll0):
    mcf = 1 - ll1 / ll0
    logging.debug('Hint: 0.2 < mcf < 0.4 is a good fit (higher value is better)')
    logging.info('McFadden R squared is: {}'.format(mcf))
    return mcf
