import logging
import typing
from os.path import expanduser as xu

import allegro_api.api
import zeep
from tinydb import TinyDB

import carscanner.allegro
from carscanner import chunks, CarOffersBuilder, CarOfferBuilder
from carscanner.allegro import CarscannerAllegro as Allegro
from carscanner.dao import CriteriaDao, CarMakeModelDao, VoivodeshipDao, CarOfferDao

logger = logging.getLogger(__name__)


class OfferService:
    def __init__(self, allegro: Allegro, criteria_dao, car_offers_builder: CarOffersBuilder, car_offer_dao):
        self._allegro = allegro

        self.criteria_dao = criteria_dao
        self.car_offers_builder = car_offers_builder
        self.car_offer_dao: CarOfferDao = car_offer_dao

    def _get_offers_for_criteria(self, crit: carscanner.dao.Criteria) -> typing.List[
        allegro_api.models.ListingOffer]:
        data: allegro_api.models.ListingResponse = self._allegro.get_listing(
            {'category.id': crit.category_id, 'fallback': False,
             # 'include': ['-all', 'items', 'searchMeta'],
             'parameter.215882': 272070,  # oferta dotyczy sprzedaży
             'parameter.11323': 2,  # stan = używane
             'startingTime': 'P2D',  # ostatnie 2 dni
             'parameter.178': '1',  # uszkodzone = nie
             'limit': 100}
        )

        return data.items.promoted + data.items.regular

    def handle_listing(self, offers: typing.List[allegro_api.models.ListingOffer]):
        pass

    def get_offers(self):
        for crit in self.criteria_dao.all():
            items = self._get_offers_for_criteria(crit)
            car_offers = self.car_offers_builder.to_car_offers(items)
            self._get_items_info(car_offers)

    def _get_items_info(self, items: typing.Dict[int, CarOfferBuilder]):
        offer_ids = list(items.keys())
        for chunk in chunks(offer_ids, self._allegro.get_items_info.items_limit):

            offer_ext: zeep.xsd.CompoundValue = self._allegro.get_items_info(itemsIdArray=chunk, getDesc=1,
                                                                             getImageUrl=1,
                                                                             getAttribs=1)
            for value in offer_ext.arrayItemListInfo.item:
                logging.debug(value.itemInfo.itId)
                items[str(value.itemInfo.itId)].update_from_item_info_struct(value)

        self.car_offer_dao.insert_multiple([builder.c for builder in items.values()])


if __name__ == '__main__':
    carscanner.configure_logging()

    client = carscanner.allegro.get_client()

    with TinyDB(xu('~/.allegro/data/static.json'), indent=2) as static_db, TinyDB(xu('~/.allegro/data/cars.json'),
                                                                                  indent=2) as db:
        criteria_dao = CriteriaDao(static_db)
        voivodeship_dao = VoivodeshipDao(static_db)
        car_make_mode_dao = CarMakeModelDao(static_db)
        car_offers_builder = CarOffersBuilder(voivodeship_dao, car_make_mode_dao)
        car_offer_dao = CarOfferDao(db)
        offer_service = OfferService(client, criteria_dao, car_offers_builder, car_offer_dao)

        offer_service.get_offers()
