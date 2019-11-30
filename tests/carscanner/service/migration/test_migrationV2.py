from unittest import TestCase
from unittest.mock import Mock

from carscanner.dao.meta import Metadata
from carscanner.service.migration import MigrationV2
from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage


class TestMigrationV2(TestCase):
    def test_migrate_zero(self):
        svc = MigrationV2(TinyDB(storage=MemoryStorage), Mock())

        self.assertRaises(Exception, svc.migrate)

    def test_migrate_from_v1(self):
        meta_db = TinyDB(storage=MemoryStorage)
        old_tbl: Table = meta_db.table()
        old_tbl.insert({'host': 'host', 'timestamp': 'date and time'})
        metadata_dao = Mock()
        svc = MigrationV2(meta_db, metadata_dao)

        svc.migrate()

        assert metadata_dao.meta == Metadata('host', 'date and time', 2)
