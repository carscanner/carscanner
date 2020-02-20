import datetime
from unittest import TestCase

from mongomock import MongoClient, Collection

from carscanner.dao import CarOfferDao
from carscanner.dao.car_offer import _K_ACTIVE, _K_FIRST_SPOTTED, _K_ID, _K_LAST_SPOTTED


class TestCarOfferDao(TestCase):
    def test_search_by_year_between_and_mileage_lt(self):
        dao = CarOfferDao(self._db().vehicle)
        dao.search_by_year_between_and_mileage_lt(1, 2, 3)

    def test_all(self):
        dao = CarOfferDao(self._db().vehicle)
        dao.all()

    def test_update_status_in_list_not_active(self):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        db = self._db()
        vehicle_col: Collection = db.vehicle
        vehicle_col.insert_one({
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_ACTIVE: False,
        })
        dao = CarOfferDao(vehicle_col)
        dao.update_status(['0'], ts)
        found = vehicle_col.find_one({_K_ID: '0'})
        self.assertEqual({
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_ACTIVE: True,
        }, found)

    def test_update_status_in_list_active(self):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        db = self._db()
        vehicle_col: Collection = db.vehicle
        doc = {
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_ACTIVE: True,
        }
        vehicle_col.insert_one(doc)
        dao = CarOfferDao(vehicle_col)
        dao.update_status(['0'], ts)
        found = vehicle_col.find_one({_K_ID: '0'})
        self.assertEqual(doc, found)

    def test_update_status_not_in_list_active(self):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        db = self._db()
        vehicle_col: Collection = db.vehicle
        vehicle_col.insert_one({
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_ACTIVE: True,
        })
        dao = CarOfferDao(vehicle_col)
        dao.update_status(['1'], ts)
        found = vehicle_col.find_one({_K_ID: '0'})
        self.assertEqual({
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_LAST_SPOTTED: ts,
            _K_ACTIVE: False,
        }, found)

    def test_update_status_not_in_list_not_active(self):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        db = self._db()
        vehicle_col: Collection = db.vehicle
        doc = {
            '_id': {
                'id': '0'
            },
            _K_FIRST_SPOTTED: ts,
            _K_ACTIVE: False,
        }
        vehicle_col.insert_one(doc)
        dao = CarOfferDao(vehicle_col)
        dao.update_status(['1'], ts)
        found = vehicle_col.find_one({_K_ID: '0'})
        self.assertEqual(doc, found)

    def _db(self):
        return MongoClient('mongodb://fakehost/mockdb').get_database()
