import datetime
from unittest import TestCase

import mongomock
from carscanner.dao import MongoTrustStore

RAW_TOKEN = {
    'access_token': 'the access token',
    'refresh_token': 'the refresh token'
}


class TestMongoTrustStore(TestCase):
    def test_load(self):
        col: mongomock.Collection = self._db().token
        col.insert_one(RAW_TOKEN.copy())

        store = MongoTrustStore(col)

        self.assertEqual('the access token', store.access_token)
        self.assertEqual('the refresh token', store.refresh_token)

    def test_save(self):
        col: mongomock.Collection = self._db().token
        store = MongoTrustStore(col)
        store.access_token = 'the access token'
        store.refresh_token = 'the refresh token'
        store.save()

        raw_token = col.find_one()

        self.assertEqual(store.access_token, raw_token['access_token'])
        self.assertEqual(store.refresh_token, raw_token['refresh_token'])
        self.assertIsInstance(raw_token['timestamp'], datetime.datetime)

    def _db(self) -> mongomock.Database:
        return mongomock.MongoClient('mongodb://fakehost/mockdb').get_database()
