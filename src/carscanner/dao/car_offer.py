import datetime
import typing
from dataclasses import dataclass
from decimal import Decimal

import tinydb


@dataclass
class CarOffer:
    id: int = None
    make: str = None
    model: str = None
    year: int = None
    mileage: int = None
    image: str = None
    url: str = None
    name: str = None
    price: Decimal = None
    first_spotted: datetime.date = datetime.date.today()
    voivodeship: str = None
    location: str = None
    imported: bool = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


class CarOfferDao:
    def __init__(self, db: tinydb.TinyDB):
        self._tbl: tinydb.database.Table = db.table('car_offer')

    def insert_multiple(self, car_offers: typing.List[CarOffer]) -> typing.List[int]:
        return self._tbl.insert_multiple([o.to_dict() for o in car_offers])
