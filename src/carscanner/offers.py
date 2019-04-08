import datetime
import logging
import typing

import allegro_api.api
import tinydb
import zeep

import carscanner.allegro
from carscanner import chunks, CarOffersBuilder, CarOfferBuilder
from carscanner.allegro import CarscannerAllegro as Allegro
from carscanner.dao import Criteria, CriteriaDao, CarMakeModelDao, VoivodeshipDao, CarOfferDao, FilterDao
from carscanner.filter import FilterService

logger = logging.getLogger(__name__)


class OfferService:
    _filter_template = {
        'Oferta dotyczy': 'sprzedaż',
        'Stan': "używane",
        'wystawione w ciągu': "2 dni",
        "Uszkodzony": "Nie"
    }
    search_params = {
        'fallback': False,
        'include': ['-all', 'items', 'searchMeta'],
        'limit': 100
    }

    def __init__(self, allegro: Allegro, criteria_dao, car_offers_builder: CarOffersBuilder, car_offer_dao,
                 filter_service, ts):
        self._allegro = allegro

        self.criteria_dao = criteria_dao
        self.car_offers_builder = car_offers_builder
        self.car_offer_dao: CarOfferDao = car_offer_dao
        self.filter_service: FilterService = filter_service
        self.timestamp: datetime.datetime = ts

    def _get_offers_for_criteria(self, crit: Criteria) -> typing.List[allegro_api.models.ListingOffer]:

        data: allegro_api.models.ListingResponse = self._allegro.get_listing(self._search_params(crit))

        logger.info('total %d, this run %d', data.search_meta.available_count,
                    len(data.items.promoted) + len(data.items.regular))
        return data.items.promoted + data.items.regular

    def _search_params(self, crit: Criteria) -> dict:
        result = OfferService.search_params.copy()
        result.update(self.filter_service.transform_filters(crit.category_id, OfferService._filter_template))
        result['category.id'] = crit.category_id

        return result

    def get_offers(self):
        for crit in self.criteria_dao.all():
            items = self._get_offers_for_criteria(crit)
            item_ids = [item.id for item in items]

            existing = self.car_offer_dao.search_existing_ids(item_ids)
            self.car_offer_dao.update_last_spotted(existing, self.timestamp)

            # get non-existing ids
            new_items = [item for item in items if item.id not in existing]

            # pull their details
            car_offers = self.car_offers_builder.to_car_offers(new_items)
            self._get_items_info(car_offers)

    def _get_items_info(self, items: typing.Dict[str, CarOfferBuilder]):
        offer_ids = list(items.keys())
        for chunk in chunks(offer_ids, self._allegro.get_items_info.items_limit):

            offer_ext: zeep.xsd.CompoundValue = self._allegro.get_items_info(itemsIdArray=chunk, getDesc=1,
                                                                             getImageUrl=1,
                                                                             getAttribs=1)
            for value in offer_ext.arrayItemListInfo.item:
                logger.debug(value.itemInfo.itId)
                items[str(value.itemInfo.itId)].update_from_item_info_struct(value)

        self.car_offer_dao.insert_multiple([builder.c for builder in items.values()])


def _update_meta(db, ts):
    import platform
    from tinydb import Query

    tbl = db.table(db.DEFAULT_TABLE)
    meta = {
        'timestamp': ts.isoformat(),
        'host': platform.node()
    }
    tbl.upsert(meta, Query())


def _report_meta(db):
    old_meta = db.get(tinydb.Query())
    if old_meta:
        logger.info('Last run at %s on %s', old_meta['timestamp'], old_meta['host'])
    else:
        logger.info('First run')


if __name__ == '__main__':
    from os.path import expanduser as xu
    from tinydb import TinyDB

    carscanner.configure_logging()

    client = carscanner.allegro.get_client()

    with TinyDB(xu('~/.allegro/data/static.json'), indent=2) as static_db, \
            TinyDB(xu('~/.allegro/data/cars.json'), indent=2) as db, \
            TinyDB(storage=tinydb.storages.MemoryStorage) as mem_db:
        _report_meta(db)

        ts = datetime.datetime.utcnow()
        _update_meta(db, ts)

        criteria_dao = CriteriaDao(static_db)
        voivodeship_dao = VoivodeshipDao(static_db)
        car_make_mode_dao = CarMakeModelDao(static_db)
        car_offers_builder = CarOffersBuilder(voivodeship_dao, car_make_mode_dao)
        car_offer_dao = CarOfferDao(db)
        filter_service = FilterService(client, FilterDao(mem_db), criteria_dao)
        offer_service = OfferService(client, criteria_dao, car_offers_builder, car_offer_dao, filter_service, ts)

        filter_service.load_parameters()
        offer_service.get_offers()
