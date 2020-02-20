import datetime
import logging
import typing
from decimal import Decimal

import allegro_api
import zeep.xsd

from carscanner.dao import CarMakeModelDao, CarOffer, VoivodeshipDao
from .make_model import derive_model

log = logging.getLogger(__name__)

_KEY_YEAR = 'Rok produkcji'
_KEY_MILEAGE = 'Przebieg'
_KEY_ORIGIN = 'Pochodzenie'
_KEY_MAKE = 'Marka'
_KEY_FUEL = 'Rodzaj paliwa'
_KEY_COUNTRY_ORIGIN = "Kraj pochodzenia"


class CarOffersBuilder:
    def __init__(self, voivodeship_dao: VoivodeshipDao, car_make_model: CarMakeModelDao, ts: datetime.datetime):
        self._voivodeship_dao = voivodeship_dao
        self._car_make_model = car_make_model
        self.ts = ts

    def new_car_offer(self):
        return CarOffer(first_spotted=self.ts)

    @staticmethod
    def update_from_listing_model(car: CarOffer, model):
        car.id = model.id
        car.name = model.name

        price = model.selling_mode.price.amount
        if not isinstance(price, str):
            log.warning("price %s (%s) is not a string for ID = %s", type(price), price, model.id)
        car.price = Decimal(str(price))

        car.url = 'https://allegro.pl/oferta/' + model.id

    def update_from_item_info_struct(self, car: CarOffer, o: zeep.xsd.valueobjects.CompoundValue):
        try:
            _update_from_item_cats(car, o.itemCats.item)
            _update_from_item_info_attributes(car, {a.attribName: a.attribValues.item for a in o.itemAttribs.item})
            self._update_from_item_info(car, o.itemInfo)
            if o.itemImages is not None:
                _update_from_item_images(car, o.itemImages.item)
        except ValueError as x:
            raise ValueError(car.id, *x.args) from None

    def _update_from_item_info(self, car: CarOffer, o: zeep.xsd.valueobjects.CompoundValue):
        assert car.id == str(o.itId)

        car.location = o.itLocation
        if o.itState is not None and o.itState != 0:
            car.voivodeship = self._voivodeship_dao.get_name_by_id(o.itState)
        if car.make is not None and car.model is None:
            car.model = self._derive_car_model(o, car.make)

    def _derive_car_model(self, item_info: zeep.xsd.CompoundValue, make: str):
        return derive_model(self._car_make_model, make, item_info.itName, item_info.itDescription)

    def _model_to_car(self, model: allegro_api.models.ListingOffer) -> CarOffer:
        result = self.new_car_offer()
        CarOffersBuilder.update_from_listing_model(result, model)
        return result

    def to_car_offers(self, offers: typing.List[allegro_api.models.ListingOffer]) -> typing.Dict[str, CarOffer]:
        return {i.id: self._model_to_car(i) for i in offers}


def _update_from_item_cats(car: CarOffer, cats: list):
    cat_names = [cat.catName for cat in cats]
    if 'Osobowe' in cat_names and 'Osobowe' != cat_names[-1]:
        idx = cat_names.index('Osobowe')
        if len(cat_names) <= idx + 1:
            return
        make = cat_names[idx + 1]
        if make != 'Inne':
            car.make = make
            if len(cat_names) <= idx + 2:
                return
            model = cat_names[idx + 2]
            if model != 'Inne':
                car.model = model


def _update_from_item_info_attributes(car: CarOffer, d: typing.Dict[str, typing.List[str]]):
    if _KEY_YEAR in d:
        car.year = int(d[_KEY_YEAR][0])
    if _KEY_MILEAGE in d:
        car.mileage = int(d[_KEY_MILEAGE][0])
    if _KEY_ORIGIN in d:
        car.imported = d[_KEY_ORIGIN][0] == 'import'
    elif _KEY_COUNTRY_ORIGIN in d:
        car.imported = d[_KEY_COUNTRY_ORIGIN] != 'Polska'
    if _KEY_MAKE in d:
        car.make = d[_KEY_MAKE][0]
    if _KEY_FUEL in d:
        car.fuel = d[_KEY_FUEL][0]


def _update_from_item_images(car: CarOffer, o: typing.List[zeep.xsd.CompoundValue]):
    car.image = _get_image(o, 2)


def _get_image(images: typing.List[zeep.xsd.CompoundValue], image_type) -> typing.Optional[str]:
    for img in images:
        if img.imageType == image_type:
            return img.imageUrl
    else:
        return None
