import tempfile
from pathlib import Path
from unittest import TestCase

from tinydb import TinyDB, Query
from tinydb.database import Table
from tinydb.storages import MemoryStorage

from carscanner.dao.car_offer import VEHICLE_V1, VEHICLE_V3
from carscanner.dao.meta import META_V2, Metadata
from carscanner.service.migration import MigrationV3


class TestMigrationV3(TestCase):

    def test_migrate_from_v2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_path = Path(tmp)
            with TinyDB(root_path / 'cars.json') as old_db:
                meta_tbl: Table = old_db.table(META_V2)
                meta_tbl.insert({'host': 'host', 'timestamp': 'timestamp', 'version': 2})

                old_tbl: Table = old_db.table(VEHICLE_V1)
                ts = 0
                ts2 = 86400
                old_tbl.insert_multiple([
                    {'id': 1, 'first_spotted': ts},
                    {'id': 2, 'first_spotted': ts},
                    {'id': 3, 'first_spotted': ts2},
                    {'id': 4, 'first_spotted': ts2}
                ])

                with TinyDB(storage=MemoryStorage) as new_db:
                    svc = MigrationV3(old_db, new_db, root_path)

                svc.migrate()

                new_tbl = new_db.table(VEHICLE_V3)
                self.assertEqual(4, len(new_tbl))
                docs = new_tbl.all()
                self.assertIn({'id': 1, 'first_spotted': ts}, docs)
                self.assertIn({'id': 2, 'first_spotted': ts}, docs)
                self.assertIn({'id': 3, 'first_spotted': ts2}, docs)
                self.assertIn({'id': 4, 'first_spotted': ts2}, docs)

                meta = Metadata(**meta_tbl.get(Query()))

                self.assertEqual(3, meta.version)
