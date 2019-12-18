import dataclasses
import datetime
import decimal
import typing

import tinydb

from carscanner.utils import datetime_to_unix, unix_to_datetime

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

    def is_valid(self) -> bool:
        return self.year is not None and self.mileage is not None


class CarOfferDao:
    def __init__(self, db: tinydb.TinyDB):
        self._tbl: tinydb.database.Table = db.table(VEHICLE_V3)

    def insert_multiple(self, car_offers: typing.Iterable[CarOffer]) -> typing.List[int]:
        return self._tbl.insert_multiple(o.to_dict() for o in car_offers)

    def _search_ids(self, cond) -> typing.List[str]:
        return [d['id'] for d in self._tbl.search(cond)]

    def search_existing_ids(self, ids: typing.List[str]) -> typing.List[str]:
        return self._search_ids(tinydb.Query().id.one_of(ids))

    def update_last_spotted(self, ids: typing.List[str], timestamp: datetime.datetime) -> typing.List[int]:
        return self._tbl.update({_K_LAST_SPOTTED: datetime_to_unix(timestamp)}, tinydb.Query().id.one_of(ids))

    def search_by_last_spotted_and_year_gte(self, ts: int, min_year: int) -> typing.List[CarOffer]:
        q = tinydb.Query()
        docs = self._tbl.search((q.last_spotted == ts) & (q.year >= min_year))
        return [CarOffer.from_dict(d) for d in docs]

    def search_by_year_between_and_mileage_lt(self, min_year: int, max_year, mileage: int) -> typing.List[CarOffer]:
        q = tinydb.Query()
        docs = self._tbl.search(
            (q.year >= min_year) &
            (q.year < max_year) &
            (q.mileage < mileage)
        )
        return [CarOffer.from_dict(d) for d in docs]
