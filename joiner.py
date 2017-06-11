import csv
import datetime

# Any1 has prime, all same prodid, shipping_time_prime,shipping_time_standard


def read_files():
    market_situations = []
    sales = []
    with open('marketSituation.csv', 'r') as csvfile:
        fieldnames = ['amount', 'merchant_id', 'offer_id', 'price', 'prime', 'product_id', 'quality', ' shipping_time_prime', 'shipping_time_standard', 'timestamp', 'triggering_merchant_id', 'uid']
        situation_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for situation in situation_reader:
            market_situations.append(situation)

    with open('buyOffer.csv', 'r') as csvfile:
        fieldnames = ['amount', 'consumer_id', 'http_code', 'left_in_stock', 'merchant_id', 'offer_id', 'price', 'product_id', 'quality', 'timestamp', 'uid']
        sales_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for sale in sales_reader:
            sales.append(sale)
    return market_situations, sales


def join(market_situations, sales):

    # Layout: [price - float, pricerank1 - int, quality - int]
    eventvector = []
    sale_events = []
    offers = dict()

    sales_counter = 0
    price_rank = 0
    quality = 0
    price = -1

    for idx, situation in enumerate(market_situations):
        timestamp_market = to_ms(situation['timestamp'])

        offers[situation['offer_id']] = (situation['price'], situation['quality'])

        # TODO @toni: Avoid list index out of range error, remove funny try, except block
        try:
            if len(market_situations) >= idx + 1 and sales_counter < len(sales) and to_ms(market_situations[idx + 1]['timestamp']) > to_ms(sales[sales_counter]['timestamp']):
                sales_current_situation = 0
                while to_ms(sales[sales_counter]['timestamp']) < timestamp_market:
                    price = sales[sales_counter]['price']
                    price_rank = calculate_price_rank(offers, price)
                    quality = sales[sales_counter]['quality']
                    sales_counter += 1
                    sales_current_situation += 1
                sale_events.append(sales_current_situation)
            else:
                sale_events.append(0)

        except Exception:
            pass
        eventvector.append([float(price), price_rank, quality])

    # For debugging
    # with open('vector.txt', 'w') as v:
    #     v.write(eventvector.__str__())

    # with open('events.txt', 'w') as e:
    #     e.write(sale_events.__str__())


def to_ms(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")


def calculate_price_rank(offers, own_price):
    price_rank = 1
    for price, quality in list(offers.values()):
        if own_price > price:
            price_rank += 1
    return price_rank

if __name__ == '__main__':
    join(read_files())
