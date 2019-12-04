from unittest import TestCase

from tinydb import TinyDB, Query
from tinydb.database import Table
from tinydb.storages import MemoryStorage

from carscanner.dao.meta import META_V2
from carscanner.service.migration import MigrationV2


class TestMigrationV2(TestCase):
    def test_migrate_from_v1(self):
        with TinyDB(storage=MemoryStorage) as meta_db:
            old_tbl: Table = meta_db.table()
            old_tbl.insert({'host': 'host', 'timestamp': 'date and time'})
            svc = MigrationV2(meta_db)

            svc.migrate()

            self.assertEqual(0, len(old_tbl))
            new_tbl: Table = meta_db.table(META_V2)
            new_meta = new_tbl.get(Query())

            self.assertEqual({'host': 'host', 'timestamp': 'date and time', 'version': 2}, new_meta)
