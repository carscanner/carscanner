import logging
import typing
from urllib.parse import parse_qs

import pyramid.request

from carscanner.dao import CarOfferDao

log = logging.getLogger(__name__)


def search_vehicles(car_offer_dao: CarOfferDao) -> typing.Callable:
    def run(request: pyramid.request.Request):
        log.info('search %s', request.query_string)
        query = parse_qs(request.query_string)
        if 'q' not in query.keys():
            return []
        tokens = query['q']
        if len(tokens) == 0:
            return []
        tokens = tokens[0].split(' ')
        log.info('search %s', tokens)
        return [translate(d) for d in car_offer_dao.find_active_by_make_or_model(tokens)]

    return run


def translate(bs: dict) -> dict:
    return {
        'image': bs['image'],
        'link': bs['url'],
        'voivodeship': bs['voivodeship'],
        'location': bs['location'],
        'make': bs['make'],
        'mileage': bs['mileage'],
        'model': bs['model'],
        'name': bs['name'],
        'price': int(bs['price'].to_decimal()),
        'year': bs['year'],
        'imported': bs['imported'],
    }
