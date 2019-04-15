import datetime
import decimal
from unittest import TestCase

from carscanner.dao import CarOffer


class TestCarOffer(TestCase):
    def test_to_dict(self):
        ts = datetime.datetime.utcnow()
        a = CarOffer(ts, ts, price=decimal.Decimal("1"))
        d = a.to_dict()
        self.assertIsInstance(d['price'], str)
        self.assertIsInstance(d['first_spotted'], int)

    def test_from_dict(self):
        o = CarOffer.from_dict({'id': '1', 'first_spotted': 1554422400, 'last_spotted': 1554422400, 'price': '2'})
        self.assertEqual('1', o.id)
        self.assertEqual(datetime.datetime(2019, 4, 5, 2, 0), o.first_spotted)
        self.assertEqual(decimal.Decimal(2), o.price)
