import datetime
import logging
import pathlib
import typing

import allegro_api.models
import zeep
import zeep.exceptions

from .allegro import CarscannerAllegro
from carscanner.car_offer import CarOffersBuilder, CarOfferBuilder
from carscanner.dao import Criteria, CarOfferDao
from carscanner.filter import FilterService
from carscanner.utils import chunks, datetime_to_unix

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
        'sort': '-startTime'
    }

    def __init__(self, allegro: CarscannerAllegro, criteria_dao, car_offers_builder: CarOffersBuilder, car_offer_dao,
                 filter_service, ts):
        self._allegro = allegro

        self.criteria_dao = criteria_dao
        self.car_offers_builder = car_offers_builder
        self.car_offer_dao: CarOfferDao = car_offer_dao
        self.filter_service: FilterService = filter_service
        self.timestamp: datetime.datetime = ts

    def _get_offers_for_criteria(self, crit: Criteria) -> typing.Iterable[typing.List[allegro_api.models.ListingOffer]]:
        offset = 0
        while True:
            data = self._allegro.get_listing(self._search_params(crit, offset))

            result = data.items.promoted + data.items.regular

            logger.info('get_listing: total %d, this run %d, offset %d', data.search_meta.available_count, len(result),
                        offset)
            yield result

            offset += len(result)
            if offset >= data.search_meta.available_count:
                break

    def _search_params(self, crit: Criteria, offset=0) -> dict:
        result = OfferService.search_params.copy()
        result.update(self.filter_service.transform_filters(crit.category_id, OfferService._filter_template))
        result['category.id'] = crit.category_id
        result['offset'] = str(offset)
        result['limit'] = str(self._allegro.get_listing.limit_max)

        return result

    def get_offers(self):
        items = []
        for crit in self.criteria_dao.all():
            for crit_items in self._get_offers_for_criteria(crit):
                items.extend(crit_items)

        item_ids = [item.id for item in items]

        existing = self.car_offer_dao.search_existing_ids(item_ids)
        self.car_offer_dao.update_last_spotted(existing, self.timestamp)

        # get non-existing ids
        new_items = [item for item in items if item.id not in existing]

        # pull their details
        car_offers = self.car_offers_builder.to_car_offers(new_items)
        for item_info_chunk in self._get_items_info(car_offers):
            for value in item_info_chunk.arrayItemListInfo.item:
                item_id = str(value.itemInfo.itId)
                car_offers[item_id].update_from_item_info_struct(value)
        self.car_offer_dao.insert_multiple([builder.c for builder in car_offers.values()])

    def _get_items_info(self, items: typing.Dict[str, CarOfferBuilder]) -> typing.Iterable[zeep.xsd.CompoundValue]:
        offer_ids = list(items.keys())
        chunk_no = 1
        from math import ceil
        chunks_count = ceil(len(offer_ids) / self._allegro.get_items_info.items_limit)
        for chunk in chunks(offer_ids, self._allegro.get_items_info.items_limit):
            logger.info('get_items_info: chunk %d out of %d', chunk_no, chunks_count)
            try:
                yield self._allegro.get_items_info(chunk, True, True, True)
            except zeep.exceptions.TransportError:
                # https://github.com/allegro/allegro-api/issues/1585
                for item_id in chunk:
                    try:
                        yield self._allegro.get_items_info([item_id], True, True, True)
                    except zeep.exceptions.TransportError as x2:
                        logger.warning('Could not fetch item (%s) info: %s', item_id, x2)
            chunk_no += 1


class OffersExporter:
    def __init__(self, car_offer_dao: CarOfferDao, meta_dao: MetadataDao):
        self._dao = car_offer_dao
        self._meta_dao = meta_dao

    def export(self, output: pathlib.Path):
        output = output.expanduser()
        ts = datetime_to_unix(self._meta_dao.get_timestamp())

        now_year = datetime.datetime.utcnow().year
        max_age = 20
        min_year = now_year - max_age

        offers = self._dao.search_by_last_spotted_and_year_gte(ts, min_year)

        model = ExportModel(ts, min_year, now_year, max_age)

        for car in offers:
            if car.mileage > 1_000_000:
                continue

            model.update(car)

        import json
        with open(output, 'wt') as f:
            json.dump(model.model(), f, indent=2)


class ExportModel:
    def __init__(self, ts: int, min_year: int, now_year: int, max_age):
        self._ts = ts
        self.min_year = min_year
        self.max_age = max_age
        self.average = AverageSeriesModel(min_year, now_year)
        self.car_series = CarSeriesModel(now_year)
        self.car_details = CarDetailsModel()

    def update(self, car: CarOffer):
        self.car_series.update(car)
        self.average.update(car)
        self.car_details.update(car)

    def model(self):
        return {
            'data': {
                'series': self.car_series.model(),
                'car_details': self.car_details.model(),
                'avg_series': self.average.model(),
                'timestamp': self._ts,
                'min_year': self.min_year,
                'max_age': self.max_age
            }
        }


class CarSeriesModel:
    def __init__(self, now_year: int):
        self._model = []
        self._now_year = now_year

    def update(self, car: CarOffer):
        self._model.append({
            'x': self._now_year - car.year,
            'y': car.mileage
        })

    def model(self):
        return self._model


class CarDetailsModel:
    def __init__(self):
        self._model = []

    def update(self, car: CarOffer):
        self._model.append({
            'name': car.name,
            'link': car.url,
            'image': car.image,
            'mileage': car.mileage,
            'year': car.year,
        })

    def model(self) -> list:
        return self._model


class AverageSeriesModel:
    def __init__(self, min_year, now_year):
        self.min_year = min_year
        self.now_year = now_year
        self.year_totals = {}
        self.year_counts = {}

    def update(self, car: CarOffer):
        y = car.year
        self.year_totals[y] = self.year_totals.get(y, 0) + car.mileage
        self.year_counts[y] = self.year_counts.get(y, 0) + 1

    def model(self):
        model = []
        for year in sorted(self.year_counts.keys()):
            total = self.year_totals[year]
            count = self.year_counts[year]
            model.append({
                'x': self.now_year - year,
                'y': int(total / count)
            })
        return model
