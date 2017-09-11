from MlMerchant import MLMerchant
from abstract_merchant import AbstractMerchant
from argument_parser import parse_arguments
from cross_validator import CrossValidator
from ml_engines.log_reg import LogisticRegressionEngine
from utils.settingsbuilder import SettingsBuilder


class LogisticRegressionMerchant(AbstractMerchant):
    def get_cross_validator(self, settings):
        return CrossValidator(settings, LogisticRegressionEngine())

    def start_merchant(self):
        settings = SettingsBuilder() \
            .with_data_file('log_reg_models.pkl') \
            .build()
        ml_merchant = MLMerchant(settings, LogisticRegressionEngine())
        ml_merchant.initialize()
        return ml_merchant


if __name__ == "__main__":
    args = parse_arguments('PriceWars Merchant doing Logistic Regression')
    if args.train and args.buy and args.merchant and args.test and args.output:
        LogisticRegressionMerchant().start_cross_validation(args)
    else:
        LogisticRegressionMerchant().start_server(args)
