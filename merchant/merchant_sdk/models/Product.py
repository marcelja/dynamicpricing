from .PricewarsObject import PricewarsObject


class Product(PricewarsObject):

    def __init__(self, uid=-1, product_id=-1, name='', price=0.0, quality=0, amount=1, signature='',
                 stock=-1, time_to_live=-1, start_of_lifetime=-1, left_in_stock=0):
        self.amount = amount
        self.name = name
        self.price = price
        self.product_id = product_id
        self.quality = quality
        self.signature = signature
        self.uid = uid
        self.stock = stock
        self.time_to_live = time_to_live
        self.start_of_lifetime = start_of_lifetime
        self.left_in_stock = left_in_stock
