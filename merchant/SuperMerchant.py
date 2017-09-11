from abc import abstractmethod

from api.api import Api
from apiabstraction import ApiAbstraction
from merchant_sdk import MerchantBaseLogic


class SuperMerchant(MerchantBaseLogic):
    def __init__(self, settings, api: ApiAbstraction = None):
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
        if api is None:
            self.api = Api(self.merchant_token, self.settings["marketplace_url"], self.settings["producer_url"])
        else:
            self.api = api

    def update_api_endpoints(self):
        """
        Updated settings may contain new endpoints, so they need to be set in the api client as well.
        However, changing the endpoint (after simulation start) may lead to an inconsistent state
        :return: None
        """
        self.api.update_marketplace_url(self.settings["marketplace_url"])
        self.api.update_producer_url(self.settings["producer_url"])

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
