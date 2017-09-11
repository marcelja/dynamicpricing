from MlMerchant import MLMerchant
from abstract_merchant import AbstractMerchant
from ml_engines.mlp import MlpEngine
from utils.argument_parser import parse_arguments
from utils.cross_validator import CrossValidator
from utils.settingsbuilder import SettingsBuilder


class MlpMerchant(AbstractMerchant):
    def get_cross_validator(self, settings):
        return CrossValidator(settings, MlpEngine())

    def start_merchant(self):
        settings = SettingsBuilder() \
            .with_data_file('mlp_models.pkl') \
            .build()
        ml_merchant = MLMerchant(settings, MlpEngine())
        ml_merchant.initialize()
        return ml_merchant


if __name__ == "__main__":
    args = parse_arguments('PriceWars Merchant doing MLP Regression')
    if args.train and args.buy and args.merchant and args.test and args.output:
        MlpMerchant().start_cross_validation(args)
    else:
        MlpMerchant().start_server(args)
