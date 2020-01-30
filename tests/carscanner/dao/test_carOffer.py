import datetime
import decimal
from unittest import TestCase

import bson

from carscanner.dao import CarOffer


class TestCarOffer(TestCase):
    def test_to_dict(self):
        ts = datetime.datetime.utcnow()
        a = CarOffer(ts, ts, price=decimal.Decimal("1"))
        d = a.to_dict()
        self.assertIsInstance(d['price'], bson.Decimal128)
        self.assertIsInstance(d['first_spotted'], datetime.datetime)

    def test_from_dict(self):
        ts = datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
        o = CarOffer.from_dict(
            {'_id': {'id': '1', 'provider': 'allegro'},
             'first_spotted': ts,
             'last_spotted': ts,
             'price': bson.Decimal128('2'),
             })
        self.assertEqual('1', o.id)
        self.assertEqual(ts, o.first_spotted)
        self.assertEqual(decimal.Decimal(2), o.price)
