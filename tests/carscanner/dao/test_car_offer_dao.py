from unittest import TestCase

from mongomock import MongoClient

from carscanner.dao import CarOfferDao


class TestCarOfferDao(TestCase):
    def test_search_by_year_between_and_mileage_lt(self):
        dao = CarOfferDao(self._db().vehicle)
        dao.search_by_year_between_and_mileage_lt(1, 2, 3)

    def test_all(self):
        dao = CarOfferDao(self._db().vehicle)
        dao.all()

    def _db(self):
        return MongoClient('mongodb://fakehost/mockdb').get_database()
