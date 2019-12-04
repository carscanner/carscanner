import tempfile
from pathlib import Path
from unittest import TestCase

from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage

from carscanner.dao.car_offer import VEHICLE_V3
from carscanner.data import VehicleShardLoader


class TestCarOffersShardLoader(TestCase):
    def test_load_zero(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl = db.table(VEHICLE_V3)
            svc = VehicleShardLoader(tbl, Path(tmp))
            svc.load()

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl: Table = db.table(VEHICLE_V3)
            root = Path(tmp) / '2019'
            root.mkdir(parents=True)
            svc = VehicleShardLoader(tbl, root)

            with TinyDB(root / 'file-1.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                tbl_shard.insert_multiple([{'data': 1}, {'data': 2}])

            with TinyDB(root / 'file-2.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                tbl_shard.insert_multiple([{'data': 3}, {'data': 4}])

            svc.load()

            self.assertEqual(4, len(tbl))
            docs = tbl.all()
            self.assertIn({'data': 1}, docs)
            self.assertIn({'data': 2}, docs)
            self.assertIn({'data': 3}, docs)
            self.assertIn({'data': 4}, docs)

    def test_close_zero(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl = db.table(VEHICLE_V3)
            svc = VehicleShardLoader(tbl, Path(tmp))
            svc.close()

    def test_close(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl: Table = db.table(VEHICLE_V3)
            root = Path(tmp) / VEHICLE_V3
            svc = VehicleShardLoader(tbl, root)

            ts = 0
            ts2 = 86400

            tbl.insert_multiple([
                {'data': 1, 'first_spotted': ts},
                {'data': 2, 'first_spotted': ts},
                {'data': 3, 'first_spotted': ts2},
                {'data': 4, 'first_spotted': ts2}
            ])

            svc.close()

            with TinyDB(root / '1970' / '01-01.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                docs = tbl_shard.all()
                self.assertEqual(2, len(docs))
                self.assertIn({'data': 1, 'first_spotted': ts}, docs)
                self.assertIn({'data': 2, 'first_spotted': ts}, docs)

            with TinyDB(root / '1970' / '01-02.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                docs = tbl_shard.all()
                self.assertEqual(2, len(docs))
                self.assertIn({'data': 3, 'first_spotted': ts2}, docs)
                self.assertIn({'data': 4, 'first_spotted': ts2}, docs)
