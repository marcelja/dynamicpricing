from .PricewarsObject import PricewarsObject


class SoldOffer(PricewarsObject):

    def __init__(self, offer_id=-1, uid=-1, product_id=-1, quality=0,
            amount_sold=0, price_sold=0.0, price=0.0, merchant_id='',
            merchant_token='', amount=0):

        self.offer_id = offer_id
        self.uid = uid
        self.product_id = product_id
        self.quality = quality
        self.amount_sold = amount_sold
        self.price_sold = price_sold
        self.price = price
        self.merchant_id = merchant_id
        self.merchant_token = merchant_token
        self.amount = amount
