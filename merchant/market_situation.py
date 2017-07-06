from merchant.timestamp_converter import TimestampConverter


class MarketSituation:
    def __init__(self, csv_row=None, kafka_row=None):
        self.amount = None
        self.merchant_id = None
        self.offer_id = None
        self.price = None
        self.prime = None
        self.product_id = None
        self.quality = None
        self.shipping_time_prime = None
        self.shipping_time_standard = None
        self.timestamp = None
        self.timestamp_object = None
        self.triggering_merchant_id = None
        self.uid = None

        if csv_row:
            self.from_csv(csv_row)
        elif kafka_row:
            self.from_kafka(kafka_row)

    def from_csv(self, csv_row):
        self.amount = csv_row[0]
        self.merchant_id = csv_row[1]
        self.offer_id = csv_row[2]
        self.price = csv_row[3]
        self.prime = csv_row[4]
        self.product_id = csv_row[5]
        self.quality = csv_row[6]
        self.shipping_time_prime = csv_row[7]
        self.shipping_time_standard = csv_row[8]
        self.timestamp = csv_row[9]
        self.timestamp_object = TimestampConverter.from_string(self.timestamp)
        self.triggering_merchant_id = csv_row[10]
        self.uid = csv_row[11]

    def from_kafka(self, kafka_row):
        self.amount = kafka_row[1]
        self.merchant_id = kafka_row[2]
        self.offer_id = kafka_row[3]
        self.price = kafka_row[4]
        self.prime = kafka_row[5]
        self.product_id = kafka_row[6]
        self.quality = kafka_row[7]
        self.shipping_time_prime = kafka_row[8]
        self.shipping_time_standard = kafka_row[9]
        self.timestamp = kafka_row[10]
        self.timestamp_object = TimestampConverter.from_string(self.timestamp)
        self.triggering_merchant_id = kafka_row[11]
