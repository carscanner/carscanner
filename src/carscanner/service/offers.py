import datetime
import logging
import typing

import allegro_api.models
import zeep
import zeep.exceptions

from carscanner.allegro import CarscannerAllegro
from carscanner.dao import CarOfferDao, Criteria
from carscanner.utils import chunks
from .car_offer import CarOffersBuilder
from .filter import FilterService

logger = logging.getLogger(__name__)


class OfferService:
    _filter_template = {
        'Oferta dotyczy': 'sprzedaż',
        'Stan': "używane",
    }
    search_params: typing.Dict[str, typing.Any] = {
        'fallback': False,
        'include': ['-all', 'items', 'searchMeta'],
        'sort': '-startTime'
    }

    def __init__(
            self, allegro: CarscannerAllegro,
            criteria_dao,
            car_offers_builder: CarOffersBuilder,
            car_offer_dao,
            filter_service,
            ts: datetime.datetime,
    ):
        self._allegro = allegro
        self.criteria_dao = criteria_dao
        self.car_offers_builder = car_offers_builder
        self.car_offer_dao: CarOfferDao = car_offer_dao
        self.filter_service: FilterService = filter_service
        self.timestamp: datetime.datetime = ts

    def _get_offers_for_criteria(self, crit: Criteria) -> typing.Iterable[typing.List[allegro_api.models.ListingOffer]]:
        offset = 0
        while True:
            try:
                data = self._allegro.get_listing(**self._search_params(crit, offset))
            except ValueError as e:
                logger.warning(e)
                params = self._search_params(crit, offset)
                params['_preload_content'] = False
                raw_data = self._allegro.get_listing(**params)
                logger.info(raw_data)
                raise

            size = len(data.items.promoted) + len(data.items.regular)
            logger.info('get_listing: cat: %s, total %d, this run %d, offset %d',
                        crit.category_id,
                        data.search_meta.available_count,
                        size,
                        offset,
                        )

            if data.items.promoted:
                yield data.items.promoted
            if data.items.regular:
                yield data.items.regular

            offset += size
            if offset >= data.search_meta.available_count:
                break

    def _search_params(self, crit: Criteria, offset=0) -> dict:
        result = OfferService.search_params.copy()
        result['dynamic_filters'] = self.filter_service.transform_filters(crit.category_id,
                                                                          OfferService._filter_template)
        result['category_id'] = crit.category_id
        result['offset'] = offset
        result['limit'] = self._allegro.get_listing.limit_max

        return result

    def get_offers(self):
        items = []
        for crit in self.criteria_dao.all():
            for crit_items in self._get_offers_for_criteria(crit):
                items.append(crit_items)
        items = [item for sublist in items for item in sublist]

        item_ids = [item.id for item in items]

        existing = self.car_offer_dao.search_existing_ids(item_ids)

        found = len(items)
        existing_len = len(existing)
        logger.info("Found vehicles: %i, known: %i, new %i", found, existing_len, found - existing_len)

        self.car_offer_dao.update_status(existing, self.timestamp)

        # get non-existing ids
        new_items = [item for item in items if item.id not in existing]

        # pull their details
        car_offers = self.car_offers_builder.to_car_offers(new_items)
        for item_info_chunk in self._get_items_info(list(car_offers.keys())):
            for value in item_info_chunk:
                item_id = str(value.itemInfo.itId)
                self.car_offers_builder.update_from_item_info_struct(car_offers[item_id], value)

        self.car_offer_dao.insert_multiple([car for car in car_offers.values() if car.is_valid()])

    def _get_items_info(self, offer_ids: typing.List[str]) -> typing.Iterable[zeep.xsd.CompoundValue]:
        chunk_no = 1
        from math import ceil
        chunks_count = ceil(len(offer_ids) / self._allegro.get_items_info.items_limit)
        for chunk in chunks(offer_ids, self._allegro.get_items_info.items_limit):
            logger.info('get_items_info: chunk %d out of %d', chunk_no, chunks_count)
            try:
                yield self._do_get_items_info(chunk)
            except zeep.exceptions.TransportError:
                # https://github.com/allegro/allegro-api/issues/1585
                for item_id in chunk:
                    try:
                        yield self._do_get_items_info([item_id])
                    except zeep.exceptions.TransportError as x2:
                        logger.warning('Could not fetch item (%s) info: %s', item_id, x2)
            chunk_no += 1

    def _do_get_items_info(self, offer_ids: typing.List[str]):
        return self._allegro.get_items_info(offer_ids, True, True, True).arrayItemListInfo.item
