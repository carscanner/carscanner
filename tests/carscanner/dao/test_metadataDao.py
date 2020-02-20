import datetime
from unittest import TestCase
from unittest.mock import Mock

from mongomock import MongoClient
from pymongo.collection import Collection

from carscanner.dao import MetadataDao
from carscanner.dao.meta import META_V2, Metadata, META_VER


class TestMetadataDao(TestCase):
    def test_init(self):
        db_mock = Mock()
        db_mock.find_one = Mock(return_value=None)
        MetadataDao(db_mock)

        db_mock.find_one.called_once_with_arguments(META_V2)

    def test_post_init_empty(self):
        svc = MetadataDao(self._db().meta)

        self.assertIsNotNone(svc._meta)

    def test_post_init_non_empty(self):
        col: Collection = self._db().meta
        raw_meta = {'host': 'a host', 'timestamp': 'a time stamp', 'version': META_VER}
        col.insert_one(raw_meta)

        svc = MetadataDao(col)

        self.assertEqual(Metadata.from_dict(raw_meta), svc._meta)

    def test_update(self):
        svc = MetadataDao(self._db().meta)

        now = datetime.datetime.now(datetime.timezone.utc)

        svc.update(now)

        self.assertEqual(now, svc.get_timestamp())

    def test_update_none(self):
        svc = MetadataDao(self._db().meta)

        self.assertRaises(AttributeError, lambda: svc.update(None))

    def test_get_timestamp(self):
        col = self._db().meta

        ts = datetime.datetime.utcnow().replace(microsecond=0)
        raw_meta = {'host': 'a host', 'timestamp': ts, 'version': META_VER}
        col.insert_one(raw_meta)

        svc = MetadataDao(col)

        self.assertEqual(ts, svc.get_timestamp())

    def _db(self):
        return MongoClient('mongodb://fakehost/mockdb').get_database()
