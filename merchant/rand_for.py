from MlMerchant import MLMerchant
from abstract_merchant import AbstractMerchant
from argument_parser import parse_arguments
from cross_validator import CrossValidator
from ml_engines.rand_for import RandomForestEngine
from utils.settingsbuilder import SettingsBuilder


class RandomForestMerchant(AbstractMerchant):
    def get_cross_validator(self, settings):
        return CrossValidator(settings, RandomForestEngine())

    def start_merchant(self):
        settings = SettingsBuilder() \
            .with_data_file('rand_for_models.pkl') \
            .build()
        ml_merchant = MLMerchant(settings, RandomForestEngine())
        ml_merchant.initialize()
        return ml_merchant


if __name__ == "__main__":
    args = parse_arguments('PriceWars Merchant doing Random Forest Regression')
    if args.train and args.buy and args.merchant and args.test and args.output:
        RandomForestMerchant().start_cross_validation(args)
    else:
        RandomForestMerchant().start_server(args)
