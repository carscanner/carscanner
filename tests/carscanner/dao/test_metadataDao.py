import datetime
from unittest import TestCase
from unittest.mock import Mock

from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage

from carscanner.dao import MetadataDao
from carscanner.dao.meta import META_V2, Metadata


class TestMetadataDao(TestCase):
    def test_init(self):
        db_mock = Mock()
        MetadataDao(db_mock)

        db_mock.table.called_once_with_arguments(META_V2)

    def test_post_init_empty(self):
        db = TinyDB(storage=MemoryStorage)
        svc = MetadataDao(db)

        svc.post_init()

        self.assertIsNotNone(svc._meta)

    def test_post_init_non_empty(self):
        db = TinyDB(storage=MemoryStorage)
        tbl: Table = db.table(META_V2)
        raw_meta = {'host': 'a host', 'timestamp': 'a time stamp', 'version': MetadataDao.META_VER}
        tbl.insert(raw_meta)

        svc = MetadataDao(db)

        svc.post_init()

        self.assertEqual(Metadata.from_dict(raw_meta), svc._meta)

    def test_update(self):
        svc = MetadataDao(TinyDB(storage=MemoryStorage))

        now = datetime.datetime.now(datetime.timezone.utc)

        svc.update(now)

        self.assertEqual(now, svc.get_timestamp())

    def test_update_none(self):
        svc = MetadataDao(TinyDB(storage=MemoryStorage))

        self.assertRaises(AttributeError, lambda: svc.update(None))

    def test_get_timestamp(self):
        db = TinyDB(storage=MemoryStorage)
        tbl: Table = db.table(META_V2)

        ts_str = '1970-01-01T00:00:00+00:00'
        raw_meta = {'host': 'a host', 'timestamp': ts_str, 'version': MetadataDao.META_VER}
        tbl.insert(raw_meta)

        svc = MetadataDao(db)

        svc.post_init()

        self.assertEqual(ts_str, svc.get_timestamp().isoformat())
