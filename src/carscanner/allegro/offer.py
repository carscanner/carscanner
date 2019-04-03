import datetime
import logging
import typing
from dataclasses import dataclass
from decimal import Decimal

import allegro_api
import zeep.xsd

from carscanner.allegro.dao import VoivodeshipDao
from carscanner.make_model import CarMakeModelDao, derive_model

log = logging.getLogger(__name__)


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
    def from_dict(cls, d):
        return cls(**d)


_KEY_YEAR = 'Rok produkcji'
_KEY_MILEAGE = 'Przebieg'
_KEY_ORIGIN = 'Pochodzenie'
_KEY_MAKE = 'Marka'


class CarOfferBuilder:
    def __init__(self, offer: allegro_api.models.ListingOffer, voivodeship_dao: VoivodeshipDao,
                 car_make_model: CarMakeModelDao):
        self._voivodeship_dao = voivodeship_dao
        self._car_make_model = car_make_model
        self.c = CarOffer()

        self._update_from_listing_model(offer)

    def _update_from_listing_model(self, model):
        car = self.c
        car.id = int(model.id)
        car.name = model.name
        car.price = Decimal(model.selling_mode.price.amount)
        car.url = 'https://allegro.pl/oferta/' + str(model.id)

    def update_from_item_info_struct(self, o: zeep.xsd.valueobjects.CompoundValue):
        try:
            self._update_from_item_info_attributes(o.itemAttribs.item)
            self._update_from_item_info(o.itemInfo)
            self._update_from_item_img_list(o.itemImages.item)
        except ValueError as x:
            raise ValueError(self.c.id, *x.args)

    def _update_from_item_info(self, o: zeep.xsd.valueobjects.CompoundValue):
        car = self.c
        assert car.id == o.itId

        car.location = o.itLocation
        car.voivodeship = self._voivodeship_dao.get_name_by_id(o.itState)
        car.model = self._derive_car_model(o)

    def _update_from_item_info_attributes(self, o: typing.List[zeep.xsd.CompoundValue]):
        d = CarOfferBuilder._attrib_list_to_dict(o)
        if _KEY_YEAR in d:
            self.c.year = d[_KEY_YEAR][0]
        if _KEY_MILEAGE in d:
            self.c.mileage = d[_KEY_MILEAGE][0]
        if _KEY_ORIGIN in d:
            self.c.imported = d[_KEY_ORIGIN][0] == 'import'
        if _KEY_MAKE in d:
            self.c.make = d[_KEY_MAKE][0]

    def _update_from_item_img_list(self, o: typing.List[zeep.xsd.CompoundValue]):
        self.c.image = self._get_image(o, 2)

    @staticmethod
    def _attrib_list_to_dict(attrib_list: list) -> dict:
        return {a.attribName: a.attribValues.item for a in attrib_list}

    @staticmethod
    def _get_image(images: typing.List[zeep.xsd.CompoundValue], image_type) -> str:
        for img in images:
            if img.imageType == image_type:
                return img.imageUrl
        else:
            return None

    def _derive_car_model(self, itemInfo: zeep.xsd.CompoundValue):
        return derive_model(self._car_make_model, self.c.make, itemInfo.itName, itemInfo.itDescription)


class CarOffersBuilder:
    def __init__(self, voivodeship_dao: VoivodeshipDao, car_make_model: CarMakeModelDao):
        self._voivodeship_dao = voivodeship_dao
        self._car_make_model = car_make_model

    def to_car_offers(self, offers: allegro_api.models.ListingResponseOffers) -> typing.List[CarOfferBuilder]:
        return [CarOfferBuilder(i, self._voivodeship_dao, self._car_make_model) for i in
                offers.promoted + offers.regular]
