import decimal
import pathlib
import typing

from carscanner.dao import CarOffer, CarOfferDao, MetadataDao
from carscanner.utils import datetime_to_unix, join_str

try:
    import ujson as json
except ModuleNotFoundError:
    import json


class ExportService:
    def __init__(self, car_offer_dao: CarOfferDao, metadata_dao: MetadataDao):
        self._dao = car_offer_dao
        self._meta_dao = metadata_dao

    def export(self, output: pathlib.Path):
        output = output.expanduser()
        now = self._meta_dao.get_timestamp()
        ts = datetime_to_unix(now)

        now_year = now.year
        max_age = 20
        min_year = now_year - max_age

        # TODO move mileage to the filter in `offers update`,
        offers = self._dao.search_by_year_between_and_mileage_lt(min_year, now_year, 1_000_000)

        model = ExportModel(ts, min_year, now_year, max_age, offers)

        with open(str(output), 'wt') as f:
            json.dump(model.model(), f, indent=2)


class ExportModel:
    def __init__(self, ts: int, min_year: int, now_year: int, max_age, offers: typing.List[CarOffer]):
        self._ts = ts
        self.min_year = min_year
        self.max_age = max_age
        self.average = AverageSeriesModel(min_year, now_year)
        self.car_series = CarSeriesModel(now_year)
        self.car_details = CarDetailsModel()

        for car in offers:
            self.average.update(car)
            if datetime_to_unix(car.last_spotted) >= ts:
                self.update(car)

    def update(self, car: CarOffer):
        self.car_series.update(car)
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
            'image': car.image,
            'link': car.url,
            'location': join_str(', ', car.voivodeship, car.location),
            'make': car.make,
            'mileage': car.mileage,
            'model': car.model,
            'name': car.name,
            'price': int(car.price.to_integral_value(decimal.ROUND_DOWN)),
            'year': car.year,
            'imported': car.imported,
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
