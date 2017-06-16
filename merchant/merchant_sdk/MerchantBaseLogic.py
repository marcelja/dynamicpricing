from abc import ABCMeta, abstractmethod

import traceback
import threading
import time
import hashlib
import base64
import os

base_settings = {}


class MerchantBaseLogic:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.settings = {}
        self.interval = 5
        self.thread = None
        self.state = 'initialized'

    @staticmethod
    def calculate_id(token):
        return base64.b64encode(hashlib.sha256(token.encode('utf-8')).digest()).decode('utf-8')

    @staticmethod
    def get_marketplace_url():
        marketplace_url = os.getenv('PRICEWARS_MARKETPLACE_URL', 'http://vm-mpws2016hp1-04.eaalab.hpi.uni-potsdam.de:8080/marketplace')
        if not marketplace_url.startswith('http://'):
            marketplace_url = 'http://' + marketplace_url
        return marketplace_url

    @staticmethod
    def get_producer_url():
        producer_url = os.getenv('PRICEWARS_PRODUCER_URL', 'http://vm-mpws2016hp1-03.eaalab.hpi.uni-potsdam.de')
        if not producer_url.startswith('http://'):
            producer_url = 'http://' + producer_url
        return producer_url

    @staticmethod
    def get_kafka_reverse_proxy_url():
        url = os.getenv('PRICEWARS_KAFKA_REVERSE_PROXY_URL', 'http://vm-mpws2016hp1-05.eaalab.hpi.uni-potsdam.de:8001')
        if not url.startswith('http://'):
            url = 'http://' + url
        return url

    '''
        Threading Logic
    '''

    def run_logic_loop(self):
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True  # Demonize thread
        self.thread.start()  # Start the execution

    def run(self):
        """ Method that should run forever """
        while True:
            if self.state == 'running':
                try:
                    self.interval = self.execute_logic() or self.interval
                except Exception as e:
                    print('error on merchantLogic:\n', e)
                    traceback.print_exc()
                    print('safely stop Merchant')
                    self.stop()
            else:
                self.interval = 5

            time.sleep(self.interval)

    '''
        Settings and merchant controls for Web-Frontend
    '''

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        def cast_to_expected_type(key, value, def_settings=self.settings):
            if key in def_settings:
                return type(def_settings[key])(value)
            else:
                return value

        new_settings_casted = dict([
            (key, cast_to_expected_type(key, new_settings[key]))
            for key in new_settings
        ])

        self.settings.update(new_settings_casted)
        return self.settings

    def setup(self):
        """
        Use this method to:
        * fetch all your existing offers form the marketplace
        * buy products and offer them in the market
        """
        pass

    @abstractmethod
    def execute_logic(self):
        """
        Entry point for regular merchant activity
        The base logic class takes care of the possible states of the merchant,
        i.e. this method is not called when the merchant is stopping
        :return: time in seconds (float) to the next wanted execution
        """
        return self.interval

    def get_state(self):
        return self.state

    def start(self):
        if self.state == 'initialized':
            self.setup()
        self.state = 'running'

    def stop(self):
        if self.state == 'running':
            self.state = 'stopping'

    '''
        Simulation API
    '''

    @abstractmethod
    def sold_offer(self, offer_json):
        """
        Do not block execution
        :param offer_json:
        :return: does not matter, but must be in time
        """
        pass
