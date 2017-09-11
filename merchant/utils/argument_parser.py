import argparse
import logging


def parse_arguments(description: str):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.MetavarTypeHelpFormatter)
    parser.add_argument('--port',
                        type=int,
                        default=5103,
                        help='Port to bind flask App to, default is 5103')
    parser.add_argument('--train',
                        type=str,
                        help='Path to csv file for training')
    parser.add_argument('--buy',
                        type=str,
                        help='Path to buyOffer.csv')
    parser.add_argument('--merchant',
                        type=str,
                        help='Merchant ID for initial csv parsing')
    parser.add_argument('--test',
                        type=str,
                        help='Path to csv file for cross validation')
    parser.add_argument('--output',
                        type=str,
                        help='Output will be written into the spedified file')
    return parser.parse_args()
