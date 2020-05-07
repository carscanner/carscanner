import datetime
import decimal
import logging
import typing

import attr
import bson
import pymongo

log = logging.getLogger(__name__)

_K_ACTIVE = 'active'
_K_FIRST_SPOTTED = 'first_spotted'
_K_ID = '_id.id'
_K_LAST_SPOTTED = 'last_spotted'
_K_PRICE = 'price'

VEHICLE_V3 = 'vehicle'


@attr.s(slots=True, auto_attribs=True)
class CarOffer:
    first_spotted: datetime.datetime = attr.ib()

    active: bool = attr.ib(default=True)
    fuel: str = attr.ib(default=None)
    id: int = attr.ib(default=None)
    image: str = attr.ib(default=None)
    imported: bool = attr.ib(default=None)
    last_spotted: datetime.datetime = attr.ib(default=None)
    location: str = attr.ib(default=None)
    make: str = attr.ib(default=None)
    mileage: int = attr.ib(default=None)
    model: str = attr.ib(default=None)
    name: str = attr.ib(default=None)
    price: decimal.Decimal = attr.ib(default=None)
    url: str = attr.ib(default=None)
    voivodeship: str = attr.ib(default=None)
    year: int = attr.ib(default=None)

    def to_dict(self):
        result = attr.asdict(self, False)
        result[_K_PRICE] = bson.Decimal128(self.price)
        result['_id'] = {'provider': 'allegro', 'id': self.id}
        del result['id']

        return result

    @classmethod
    def from_dict(cls, d: dict):
        doc = d.copy()
        doc['id'] = d['_id']['id']
        del doc['_id']
        doc.setdefault(_K_ACTIVE, None)
        doc[_K_PRICE] = doc[_K_PRICE].to_decimal()
        return cls(**doc)

    def is_valid(self) -> bool:
        return self.year is not None and self.mileage is not None


class CarOfferDao:
    def __init__(self, col: pymongo.collection.Collection):
        self._col = col

    def insert_multiple(self, car_offers: typing.List[CarOffer]) -> typing.List[int]:
        if len(car_offers):
            return self._col.insert_many(o.to_dict() for o in car_offers).inserted_ids

    def _search_ids(self, cond) -> typing.List[str]:
        return [d['_id']['id'] for d in self._col.find(cond, {_K_ID: 1})]

    def search_existing_ids(self, ids: typing.List[str]) -> typing.List[str]:
        return self._search_ids({_K_ID: {'$in': ids}})

    def update_status(self, ids: typing.List[str], timestamp: datetime.datetime) -> typing.List[int]:
        result = self._col.update_many({
            _K_ID: {'$in': ids},
            _K_ACTIVE: {'$ne': True},
        }, {'$set': {
            _K_ACTIVE: True,
        }})

        modified_count = result.modified_count
        if modified_count != 0:
            log.info('%d inactive offers were activated', modified_count)

        return self._col.update_many(
            {
                _K_ID: {'$nin': ids},
                _K_ACTIVE: {'$ne': False},
            }, {'$set': {
                _K_ACTIVE: False,
                _K_LAST_SPOTTED: timestamp,
            }}
        ).upserted_id

    def search_by_year_between_and_mileage_lt(self, min_year: int, max_year, mileage: int) -> typing.List[CarOffer]:
        docs = self._col.find({
            _K_ACTIVE: True,
            'year': {'$gte': min_year, '$lt': max_year},
            'mileage': {"$lt": mileage},
        },
            sort=[(_K_ID, pymongo.ASCENDING)],
        )
        return [CarOffer.from_dict(d) for d in docs]

    def all(self) -> typing.Iterable[CarOffer]:
        return (CarOffer.from_dict(d) for d in self._col.find().sort([(_K_ID, 1)]))

    def find_active_by_make_or_model(self, tokens: typing.List[str]) -> typing.List[dict]:
        result = self._col.find(
            {
                _K_ACTIVE: True,
                '$or': [
                    {'make': {'$in': tokens}, },
                    {'model': {'$in': tokens}, },
                ],
            },
            limit=100,
        )
        return [obj for obj in result]
