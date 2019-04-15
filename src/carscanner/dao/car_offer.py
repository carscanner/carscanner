import dataclasses
import datetime
import decimal
import typing

import tinydb

from carscanner.utils import datetime_to_unix, unix_to_datetime

_K_PRICE = 'price'
_K_FIRST_SPOTTED = 'first_spotted'
_K_LAST_SPOTTED = 'last_spotted'


@dataclasses.dataclass
class CarOffer:
    first_spotted: datetime.date
    last_spotted: datetime.date
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
        result = self.__dict__
        if self.price is not None:
            result[_K_PRICE] = str(self.price)
        result[_K_FIRST_SPOTTED] = datetime_to_unix(self.first_spotted)
        result[_K_LAST_SPOTTED] = datetime_to_unix(self.last_spotted)

        return result

    @classmethod
    def from_dict(cls, d: dict):
        result = cls(**d)
        result.first_spotted = unix_to_datetime(d[_K_FIRST_SPOTTED])
        result.last_spotted = unix_to_datetime(d[_K_LAST_SPOTTED])
        if result.price:
            result.price = decimal.Decimal(d[_K_PRICE])
        return result


class CarOfferDao:
    def __init__(self, db: tinydb.TinyDB):
        self._tbl: tinydb.database.Table = db.table('car_offer')

    def insert_multiple(self, car_offers: typing.List[CarOffer]) -> typing.List[int]:
        return self._tbl.insert_multiple([o.to_dict() for o in car_offers])

    def _search_ids(self, cond) -> typing.List[str]:
        return [d['id'] for d in self._tbl.search(cond)]

    def search_existing_ids(self, ids: typing.List[str]) -> typing.List[str]:
        return self._search_ids(tinydb.Query().id.one_of(ids))

    def update_last_spotted(self, ids: typing.List[str], timestamp: datetime.datetime) -> typing.List[int]:
        return self._tbl.update({_K_LAST_SPOTTED: timestamp}, tinydb.Query().id.one_of(ids))
