import json
from typing import Type

from flask import Flask, request, Response
from flask_cors import CORS

from .MerchantBaseLogic import MerchantBaseLogic
from .models import SoldOffer


def json_response(obj):
    js = json.dumps(obj)
    resp = Response(js, status=200, mimetype='application/json')
    return resp


class MerchantServer:
    
    def __init__(self, merchant_logic: Type[MerchantBaseLogic], debug=False):
        self.merchant_logic = merchant_logic
        self.server_settings = {
            'debug': debug
        }

        self.app = Flask(__name__)
        CORS(self.app)

        self.register_routes()

    def log(self, *msg):
        if self.server_settings['debug']:
            print(*msg)

    '''
        Helper methods
    '''

    def get_all_settings(self):
        tmp_settings = {
            'state': self.merchant_logic.get_state()
        }
        tmp_settings.update(self.merchant_logic.get_settings())
        tmp_settings.update(self.server_settings)
        return tmp_settings

    def update_all_settings(self, new_settings):
        new_server_settings = {k: new_settings[k] for k in new_settings if k in self.server_settings}
        self.server_settings.update(new_server_settings)
        new_logic_settings = {k: new_settings[k] for k in new_settings if k in self.merchant_logic.get_settings()}
        self.merchant_logic.update_settings(new_logic_settings)

        self.log('update settings', self.get_all_settings())

    '''
        Routes
    '''

    def register_routes(self):
        self.app.add_url_rule('/settings', 'get_settings', self.get_settings, methods=['GET'])
        self.app.add_url_rule('/settings', 'put_settings', self.put_settings, methods=['PUT', 'POST'])
        self.app.add_url_rule('/settings/execution', 'set_state', self.set_state, methods=['POST'])
        self.app.add_url_rule('/sold', 'item_sold', self.item_sold, methods=['POST'])

    '''
        Endpoint definitions
    '''

    def get_settings(self):
        return json_response(self.get_all_settings())

    def put_settings(self):
        new_settings = request.json
        self.update_all_settings(new_settings)
        return json_response(self.get_all_settings())

    def set_state(self):
        next_state = request.json['nextState']
        self.log('Execution setting - next state:', next_state)

        '''
            Execution settings can contain setting change
            i.e. on 'init', merchant_url and marketplace_url is given

            EDIT: maybe remove this settings update, since 'init' is not
            supported anymore
        '''

        endpoint_setting_keys = ['merchant_url', 'marketplace_url']
        endpoint_settings = {k: request.json[k] for k in request.json if k in endpoint_setting_keys}
        self.update_all_settings(endpoint_settings)

        if next_state == 'start':
            self.merchant_logic.start()
        elif next_state == 'stop':
            self.merchant_logic.stop()

        return json_response({})

    def item_sold(self):
        try:
            sent_json = request.get_json(force=True)
            offer = SoldOffer.from_dict(sent_json)
            self.merchant_logic.sold_offer(offer)
        except Exception as e:
            self.log(e)

        return json_response({})
