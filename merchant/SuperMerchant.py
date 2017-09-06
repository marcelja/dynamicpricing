from abc import abstractmethod

from merchant_sdk import MerchantBaseLogic
from merchant_sdk.api import PricewarsRequester, MarketplaceApi, ProducerApi


class SuperMerchant(MerchantBaseLogic):
    def __init__(self, settings):
        MerchantBaseLogic.__init__(self)

        self.settings = settings

        '''
            Internal state handling
        '''
        self.execQueue = []

        '''
            Information store
        '''
        self.products = {}
        self.offers = {}

        '''
            Predefined API token
        '''
        self.merchant_id = settings["merchant_id"]
        self.merchant_token = settings["merchant_token"]
        '''
            Setup API
        '''
        PricewarsRequester.add_api_token(self.merchant_token)
        self.marketplace_api = MarketplaceApi(host=self.settings["marketplace_url"])
        self.producer_api = ProducerApi(host=self.settings["producer_url"])

    def update_api_endpoints(self):
        """
        Updated settings may contain new endpoints, so they need to be set in the api client as well.
        However, changing the endpoint (after simulation start) may lead to an inconsistent state
        :return: None
        """
        self.marketplace_api.host = self.settings["marketplace_url"]
        self.producer_api.host = self.settings["producer_url"]

    '''
        Implement Abstract methods / Interface
    '''

    @abstractmethod
    def execute_logic(self):
        pass

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        MerchantBaseLogic.update_settings(self, new_settings)
        self.update_api_endpoints()
        return self.settings

    def sold_offer(self, offer):
        pass
