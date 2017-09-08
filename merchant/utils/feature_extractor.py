from typing import List

from merchant_sdk.models import Offer


def extract_features(offer_id: str, offer_list: List[Offer], universal_features: bool, product_prices: dict):
    if universal_features:
        return __extract_universal_features(offer_id, offer_list)
    else:
        return __extract_product_specific_features(offer_id, offer_list, product_prices)


def __extract_universal_features(offer_id: str, offer_list: List[Offer]):
    current_offer = [x for x in offer_list if offer_id == x.offer_id][0]
    other_offers = [x for x in offer_list if offer_id != x.offer_id]

    ranks = __calculate_ranks(current_offer, other_offers)
    price_differences = __calculate_price_differences(float(current_offer.price),
                                                      other_offers)

    # if new features are added, update NUM_OF_UNIVERSAL_FEATURES variable!
    features = [ranks[0],  # price_rank
                # ranks[1],  # quality_rank
                # ranks[2],  # shipping_time_rank
                len(offer_list),  # amount_offers
                # 1 if current_offer.prime == 'True' else 0,  # prime
                price_differences[1],  # price_diff_to_min_in_%
                price_differences[3],  # price_diff_to_2nd_min_in_%
                price_differences[5],  # price_diff_to_3rd_min_in_%
                ]
    return features


def __extract_product_specific_features(offer_id: str, offer_list: List[Offer], product_prices: dict):
    current_offer: Offer = [x for x in offer_list if offer_id == x.offer_id][0]
    other_offers: List = [x for x in offer_list if offer_id != x.offer_id]

    ranks = __calculate_ranks(current_offer, other_offers)
    price_differences = __calculate_price_differences(float(current_offer.price),
                                                      other_offers)

    # if new features are added, update NUM_OF_PRODUCT_SPECIFIC_FEATURES variable!
    features = [ranks[0],  # price_rank
                # ranks[1],  # quality_rank
                # ranks[2],  # shipping_time_rank
                len(offer_list),  # amount_offers
                # 1 if current_offer.prime == 'True' else 0,  # prime
                price_differences[1],  # price_diff_to_min_in_%
                price_differences[3],  # price_diff_to_2nd_min_in_%
                price_differences[5],  # price_diff_to_3rd_min_in_%

                # disable following for universal model
                float(current_offer.price),  # price
                int(current_offer.quality),  # quality
                int(current_offer.shipping_time['standard']),  # shipping_time
                __calculate_average_price(other_offers),  # avg_price
                __calculate_average_price(offer_list),  # avg_price_with_current_offer
                __calculate_average_price_from_price_list(product_prices.get(current_offer.product_id)),  # average sale prices
                price_differences[0],  # price_diff_to_min
                price_differences[2],  # price_diff_to_2nd_min
                price_differences[4]  # price_diff_to_3rd_min
                ]
    return features


def __calculate_ranks(current_offer, other_offers):
    price_rank = 1
    quality_rank = 1
    shipping_time_rank = 1

    for oo in other_offers:
        if float(oo.price) < float(current_offer.price):
            price_rank += 1
        if int(oo.quality) < int(current_offer.quality):
            quality_rank += 1
        if int(oo.shipping_time['standard']) < int(current_offer.shipping_time['standard']):
            shipping_time_rank += 1
    return price_rank, quality_rank, shipping_time_rank


def __calculate_price_differences(current_price, other_offers):
    price_list = sorted([float(x.price) for x in other_offers])
    result = []
    for i in [0, 1, 2]:
        if i >= len(price_list):
            result.extend([0, 0])
            continue
        diffs = __calculate_price_difference(current_price, price_list[i],
                                             price_list[-1])
        result.extend(diffs)
    return result


def __calculate_price_difference(price1, price2, max_price):
    diff = price1 - price2
    if price1 <= price2:
        diff_in_percent = 0.
    elif price1 >= max_price:
        diff_in_percent = 1.
    else:
        diff_in_percent = (price1 - price2) / (max_price - price2)
    return [diff, diff_in_percent]


def __calculate_average_price(offers):
    price_list = [float(x.price) for x in offers]
    return __calculate_average_price_from_price_list(price_list)


def __calculate_average_price_from_price_list(price_list: List):
    if price_list and len(price_list) != 0:
        return sum(price_list) / len(price_list)
    else:
        return 0
