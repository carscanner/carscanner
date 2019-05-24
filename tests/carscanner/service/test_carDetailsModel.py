import decimal
from unittest import TestCase

from carscanner import CarOffer
from carscanner.service.export import CarDetailsModel
from carscanner.utils import now


class TestCarDetailsModel(TestCase):
    def test_update(self):
        ts = now()
        o = CarOffer(ts, ts)
        o.id = 1
        o.location = 'location'
        o.voivodeship = 'voivodeship'
        o.price = decimal.Decimal('42')
        o.mileage = 123
        o.name = 'name'
        o.year = 2000
        o.make = 'make'
        o.model = 'model'
        o.image = 'image url'
        o.url = 'offer url'
        o.imported = True

        model = CarDetailsModel()

        model.update(o)

        export = model.model()

        expected = [{
            'image': 'image url',
            'link': 'offer url',
            'location': 'voivodeship, location',
            'make': 'make',
            'mileage': 123,
            'model': 'model',
            'name': 'name',
            'price': 42,
            'year': 2000,
            'imported': True
        }]

        self.assertEqual(expected, export)
