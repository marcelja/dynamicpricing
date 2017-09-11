import logging
from abc import ABC, abstractmethod

from MlMerchant import MLMerchant
from merchant_sdk import MerchantServer
from utils.cross_validator import CrossValidator
from utils.settingsbuilder import SettingsBuilder


class AbstractMerchant(ABC):
    def start_cross_validation(self, args):
        initial_learning_parameters = {'train': args.train, 'buy': args.buy, 'merchant_id': args.merchant, 'testing_set': args.test, 'output_file': args.output}
        logging.info('Using given settings for cross validation...')
        settings = SettingsBuilder().with_initial_learning_parameters(initial_learning_parameters).build()
        cross_validator = self.get_cross_validator(settings)
        cross_validator.cross_validation()

    def start_server(self, args):
        logging.info('Not enough parameters for cross validation specified!')
        logging.info('Starting server')
        server = MerchantServer(self.start_merchant())
        app = server.app
        app.run(host='0.0.0.0', port=args.port)

    @abstractmethod
    def start_merchant(self) -> MLMerchant:
        pass

    @abstractmethod
    def get_cross_validator(self, settings) -> CrossValidator:
        pass
