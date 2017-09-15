import pickle


def load_history(file):
    with open(file, 'rb') as m:
        return pickle.load(m)


def save_training_data(data, file):
    with open(file, 'wb') as m:
        pickle.dump(data, m)


def write_calculations_to_file(probability_per_offer, file_path):
    with open(file_path, 'w') as output:
        output.write(str(probability_per_offer))


def get_buy_offer_fieldnames():
    return ['amount', 'consumer_id', 'http_code', 'left_in_stock', 'merchant_id',
            'offer_id', 'price', 'product_id', 'quality', 'timestamp', 'uid']


def get_market_situation_fieldnames():
    return ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id',
            'quality', 'shipping_time_prime', 'shipping_time_standard', 'timestamp',
            'triggering_merchant_id', 'uid']
