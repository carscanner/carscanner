import datetime
import decimal
from unittest import TestCase

import bson

from carscanner.dao import CarOffer
from carscanner.dao.car_offer import _K_PRICE, _K_FIRST_SPOTTED, _K_ACTIVE

class TestCarOffer(TestCase):
    def test_to_dict(self):
        ts = datetime.datetime.utcnow()
        a = CarOffer(ts, price=decimal.Decimal("1"))
        d = a.to_dict()
        self.assertIsInstance(d[_K_PRICE], bson.Decimal128)
        self.assertIsInstance(d[_K_FIRST_SPOTTED], datetime.datetime)
        self.assertTrue(d[_K_ACTIVE])

    def test_from_dict(self):
        ts = datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
        o = CarOffer.from_dict(
            {'_id': {'id': '1', 'provider': 'allegro'},
             _K_FIRST_SPOTTED: ts,
             _K_PRICE: bson.Decimal128('2'),
             })
        self.assertEqual('1', o.id)
        self.assertEqual(ts, o.first_spotted)
        self.assertEqual(decimal.Decimal(2), o.price)
        self.assertIsNone(o.active)
