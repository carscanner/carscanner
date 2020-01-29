import datetime
from unittest import TestCase
from unittest.mock import Mock

import bson
from mongomock import MongoClient
from pymongo.collection import Collection

from carscanner.dao import MetadataDao
from carscanner.dao.meta import META_V2, Metadata


class TestMetadataDao(TestCase):
    def test_init(self):
        db_mock = Mock()
        db_mock.find_one = Mock(return_value=None)
        MetadataDao(db_mock)

        db_mock.find_one.called_once_with_arguments(META_V2)

    def test_post_init_empty(self):
        svc = MetadataDao(MongoClient().carscanner.meta)

        self.assertIsNotNone(svc._meta)

    def test_post_init_non_empty(self):
        col: Collection = MongoClient().carscanner.meta
        raw_meta = {'host': 'a host', 'timestamp': 'a time stamp', 'version': MetadataDao.META_VER}
        col.insert_one(raw_meta)

        svc = MetadataDao(col)

        self.assertEqual(Metadata.from_dict(raw_meta), svc._meta)

    def test_update(self):
        svc = MetadataDao(MongoClient().carscanner.meta)

        now = datetime.datetime.now(datetime.timezone.utc)

        svc.update(now)

        self.assertEqual(now, svc.get_timestamp())

    def test_update_none(self):
        svc = MetadataDao(MongoClient().carscanner.meta)

        self.assertRaises(AttributeError, lambda: svc.update(None))

    def test_get_timestamp(self):
        col = MongoClient(tz_aware=True).get_database('carscanner').meta

        ts = datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
        raw_meta = {'host': 'a host', 'timestamp': ts, 'version': MetadataDao.META_VER}
        col.insert_one(raw_meta)

        svc = MetadataDao(col)

        self.assertEqual(ts, svc.get_timestamp())
