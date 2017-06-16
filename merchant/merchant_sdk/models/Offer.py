from .PricewarsObject import PricewarsObject


class Offer(PricewarsObject):

    def __init__(self, amount=1, merchant_id='', offer_id=-1, price=0.0, prime=False, product_id=-1,
                 quality=0, shipping_time={'standard': 3}, signature='', uid=-1):

        self.amount = amount
        self.merchant_id = merchant_id
        self.offer_id = offer_id
        self.price = price
        self.prime = prime
        self.product_id = product_id
        self.quality = quality
        self.shipping_time = shipping_time
        self.signature = signature
        self.uid = uid

    @staticmethod
    def from_product(product):
        return Offer(
            product_id=product.product_id,
            amount=product.amount,
            signature=product.signature,
            uid=product.uid,
            quality=product.quality,
            price=product.price
        )
