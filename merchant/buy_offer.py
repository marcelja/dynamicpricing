from timestamp_converter import TimestampConverter


class BuyOffer:
    def __init__(self, csv_row=None, kafka_row=None):
        self.amount = None
        self.consumer_id = None
        self.http_code = None
        self.left_in_stock = None
        self.merchant_id = None
        self.offer_id = None
        self.price = None
        self.product_id = None
        self.quality = None
        self.timestamp = None
        self.timestamp_object = None
        self.uid = None
        if csv_row:
            self.from_csv(csv_row)
        elif kafka_row:
            self.from_kafka(kafka_row)

    def from_csv(self, csv_row):
        self.amount = csv_row[0]
        self.consumer_id = csv_row[1]
        self.http_code = csv_row[2]
        self.left_in_stock = csv_row[3]
        self.merchant_id = csv_row[4]
        self.offer_id = csv_row[5]
        self.price = csv_row[6]
        self.product_id = csv_row[7]
        self.quality = csv_row[8]
        self.timestamp = csv_row[9]
        self.timestamp_object = TimestampConverter.from_string(self.timestamp)
        self.uid = csv_row[10]

    def from_kafka(self, kafka_row):
        self.amount = kafka_row[1]
        self.consumer_id = kafka_row[2]
        self.http_code = kafka_row[3]
        self.left_in_stock = kafka_row[4]
        self.merchant_id = kafka_row[5]
        self.offer_id = kafka_row[6]
        self.price = kafka_row[7]
        self.product_id = kafka_row[8]
        self.quality = kafka_row[9]
        self.timestamp = kafka_row[10]
        self.timestamp_object = TimestampConverter.from_string(self.timestamp)

        # {'amount': row[1], 'consumer_id': row[2], 'left_in_stock': row[4], 'merchant_id': row[5], 'offer_id': row[6], 'price': row[7], 'product_id': row[8], 'quality': row[9],
        #  'timestamp': row[10]}
