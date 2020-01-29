from unittest import TestCase

from mongomock import MongoClient

from carscanner.dao import CarOfferDao


class TestCarOfferDao(TestCase):
    def test_search_by_year_between_and_mileage_lt(self):
        mongo = MongoClient()
        dao = CarOfferDao(mongo.carscanner.vehicle)
        dao.search_by_year_between_and_mileage_lt(1, 2, 3)

    def test_all(self):
        mongo = MongoClient()
        dao = CarOfferDao(mongo.carscanner.vehicle)
        dao.all()


