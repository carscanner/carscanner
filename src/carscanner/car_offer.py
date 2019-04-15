import datetime
import logging
import typing
from decimal import Decimal

import allegro_api
import zeep.xsd

from carscanner.dao import CarMakeModelDao, CarOffer, VoivodeshipDao
from carscanner.make_model import derive_model

log = logging.getLogger(__name__)

_KEY_YEAR = 'Rok produkcji'
_KEY_MILEAGE = 'Przebieg'
_KEY_ORIGIN = 'Pochodzenie'
_KEY_MAKE = 'Marka'


class CarOfferBuilder:
    def __init__(self, offer: allegro_api.models.ListingOffer, voivodeship_dao: VoivodeshipDao,
                 car_make_model: CarMakeModelDao, ts: datetime.datetime):
        self._voivodeship_dao = voivodeship_dao
        self._car_make_model = car_make_model
        self.c = CarOffer(first_spotted=ts, last_spotted=ts)

        self._update_from_listing_model(offer)

    def _update_from_listing_model(self, model):
        car = self.c
        car.id = model.id
        car.name = model.name
        car.price = Decimal(model.selling_mode.price.amount)
        car.url = 'https://allegro.pl/oferta/' + model.id

    def update_from_item_info_struct(self, o: zeep.xsd.valueobjects.CompoundValue):
        try:
            self._update_from_item_cats(o.itemCats.item)
            self._update_from_item_info_attributes(o.itemAttribs.item)
            self._update_from_item_info(o.itemInfo)
            if o.itemImages is not None:
                self._update_from_item_imgages(o.itemImages.item)
        except ValueError as x:
            raise ValueError(self.c.id, *x.args)

    def _update_from_item_cats(self, cats: list):
        cat_names = [cat.catName for cat in cats]
        if 'Osobowe' in cat_names and 'Osobowe' != cat_names[-1]:
            idx = cat_names.index('Osobowe')
            if len(cat_names) <= idx + 1:
                return
            make = cat_names[idx + 1]
            if make != 'Inne':
                self.c.make = make
                if len(cat_names) <= idx + 2:
                    return
                model = cat_names[idx + 2]
                if model != 'Inne':
                    self.c.model = model

    def _update_from_item_info(self, o: zeep.xsd.valueobjects.CompoundValue):
        car = self.c
        assert car.id == str(o.itId)

        car.location = o.itLocation
        if o.itState is not None and o.itState != 0:
            car.voivodeship = self._voivodeship_dao.get_name_by_id(o.itState)
        if car.make is not None and car.model is None:
            car.model = self._derive_car_model(o)

    def _update_from_item_info_attributes(self, o: typing.List[zeep.xsd.CompoundValue]):
        d = CarOfferBuilder._attrib_list_to_dict(o)
        if _KEY_YEAR in d:
            self.c.year = int(d[_KEY_YEAR][0])
        if _KEY_MILEAGE in d:
            self.c.mileage = int(d[_KEY_MILEAGE][0])
        if _KEY_ORIGIN in d:
            self.c.imported = d[_KEY_ORIGIN][0] == 'import'
        if _KEY_MAKE in d:
            self.c.make = d[_KEY_MAKE][0]

    def _update_from_item_imgages(self, o: typing.List[zeep.xsd.CompoundValue]):
        self.c.image = self._get_image(o, 2)

    @staticmethod
    def _attrib_list_to_dict(attrib_list: list) -> dict:
        return {a.attribName: a.attribValues.item for a in attrib_list}

    @staticmethod
    def _get_image(images: typing.List[zeep.xsd.CompoundValue], image_type) -> typing.Optional[str]:
        for img in images:
            if img.imageType == image_type:
                return img.imageUrl
        else:
            return None

    def _derive_car_model(self, item_info: zeep.xsd.CompoundValue):
        return derive_model(self._car_make_model, self.c.make, item_info.itName, item_info.itDescription)


class CarOffersBuilder:
    def __init__(self, voivodeship_dao: VoivodeshipDao, car_make_model: CarMakeModelDao, ts: datetime.datetime):
        self._voivodeship_dao = voivodeship_dao
        self._car_make_model = car_make_model
        self._ts = ts

    def to_car_offers(self, offers: typing.List[allegro_api.models.ListingOffer]) -> typing.Dict[str, CarOfferBuilder]:
        return {i.id: CarOfferBuilder(i, self._voivodeship_dao, self._car_make_model, self._ts) for i in offers}
