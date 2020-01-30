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
        self.assertEqual(RAW_TOKEN, {k: v for k, v in raw_token.items() if k != '_id'})

    def _db(self) -> mongomock.Database:
        return mongomock.MongoClient('mongodb://fakehost/mockdb').get_database()
