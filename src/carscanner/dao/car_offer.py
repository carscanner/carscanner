import dataclasses
import datetime
import decimal
import typing

import bson
import pymongo

_K_PRICE = 'price'
_K_FIRST_SPOTTED = 'first_spotted'
_K_LAST_SPOTTED = 'last_spotted'

VEHICLE_V1 = 'car_offer'
VEHICLE_V3 = 'vehicle'


@dataclasses.dataclass
class CarOffer:
    first_spotted: datetime.datetime
    last_spotted: datetime.datetime
    id: int = None
    make: str = None
    model: str = None
    year: int = None
    mileage: int = None
    image: str = None
    url: str = None
    name: str = None
    price: decimal.Decimal = None
    voivodeship: str = None
    location: str = None
    imported: bool = None

    def to_dict(self):
        result = self.__dict__.copy()
        result[_K_PRICE] = bson.Decimal128(self.price)
        result['_id'] = {'provider': 'allegro', 'id': self.id}
        del result['id']

        return result

    @classmethod
    def from_dict(cls, d: dict):
        doc = d.copy()
        doc['id'] = d['_id']['id']
        del doc['_id']
        doc['price'] = doc['price'].to_decimal()
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
        return [d['_id']['id'] for d in self._col.find(cond, {'_id.id': 1})]

    def search_existing_ids(self, ids: typing.List[str]) -> typing.List[str]:
        return self._search_ids({'_id.id': {'$in': ids}})

    def update_last_spotted(self, ids: typing.List[str], timestamp: datetime.datetime) -> typing.List[int]:
        return self._col.update_many({'_id.id': {'$in': ids}}, {'$set': {_K_LAST_SPOTTED: timestamp}})

    def search_by_year_between_and_mileage_lt(self, min_year: int, max_year, mileage: int) -> typing.List[CarOffer]:
        docs = self._col.find({
            'year': {'$gte': min_year, '$lt': max_year},
            'mileage': {"$lt": mileage},
        },
            sort=[('_id.id', pymongo.ASCENDING)],
        )
        return [CarOffer.from_dict(d) for d in docs]

    def all(self) -> typing.Iterable[CarOffer]:
        return (CarOffer.from_dict(d) for d in self._col.find().sort([('_id.id', 1)]))
