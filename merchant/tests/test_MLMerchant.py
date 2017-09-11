from unittest import TestCase

from MlMerchant import MLMerchant
from tests.helper.ml_testengine import MlTestEngine
from utils.settingsbuilder import SettingsBuilder


class TestMLMerchant(TestCase):
    def setUp(self):
        self.tested = MLMerchant(SettingsBuilder().build(), MlTestEngine())

        # TODO
