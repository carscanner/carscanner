import datetime
import typing
from dataclasses import dataclass
from decimal import Decimal

import allegro_api
import zeep.objects
import zeep.xsd
import logging

log = logging.getLogger(__name__)


@dataclass
class CarOffer:
    id: int = None
    maker: str = None
    model: str = None
    year: int = None
    mileage: int = None
    image: str = None
    # url: str = None
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


class CarOfferBuilder(CarOffer):
    def __init__(self, offer: allegro_api.models.ListingOffer, voivodeships: list):
        super().__init__()

        self.id = int(offer.id)
        self.name = offer.name
        self.price = Decimal(offer.selling_mode.price.amount)

        self._voivodeships = voivodeships

    def handle_doShowItemInfoExtResponse(self, o: zeep.objects.doShowItemInfoExtResponse):
        self._update_from_item_info_ext(o.itemListInfoExt)
        self._update_from_item_info_attributes(o.itemAttribList.item)

    def _update_from_item_info_ext(self, o: zeep.objects.ItemInfoExt):
        assert self.id == o.itId
        self.id = o.itId
        self.name = o.name
        if o.itAdvertisementActive == 1:
            self.price = Decimal(o.itAdvertisementPrice)
        self.location = o.itLocation
        self.voivodeship = self._voivodeships[o.itState]

    def _update_from_item_info_attributes(self, o: list):
        log.debug('attributes type: %s', type(o))

        d = CarOfferBuilder._attrib_list_to_dict(o)

        self.year = d['Rok produkcji']
        self.mileage = d['Przebieg']
        self.imported = d['Pochodzenie'] != 'krajowe'

    @staticmethod
    def _attrib_list_to_dict(attrib_list: list) -> dict:
        return {a.attribName: a.attribValues.item for a in attrib_list}


class CarOffersBuilder:
    def __init__(self, voivodeships: list):
        self._voivodeships = voivodeships

    def to_car_offers(self, offers: allegro_api.models.ListingResponseOffers) -> typing.List[CarOfferBuilder]:
        return [CarOfferBuilder(i, self._voivodeships) for i in offers.promoted + offers.regular]
