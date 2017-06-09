from .PricewarsObject import PricewarsObject


class ApiError(PricewarsObject):

    def __init__(self, code=-1, message='', fields=''):
        self.code = code
        self.message = message
        self.fields = fields


class ApiException(Exception):

    def __init__(self, json_reponse):
        self.error = ApiError.from_dict(json_reponse)
