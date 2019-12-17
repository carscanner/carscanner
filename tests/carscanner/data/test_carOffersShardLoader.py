import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, call

from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage

from carscanner.dao import VehicleShard
from carscanner.dao.car_offer import VEHICLE_V3
from carscanner.data import VehicleShardLoader


class TestCarOffersShardLoader(TestCase):
    def test_load_zero(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl = db.table(VEHICLE_V3)
            vehicle_shard_dao = Mock()
            vehicle_shard_dao.all = Mock(return_value=[])
            svc = VehicleShardLoader(tbl, vehicle_shard_dao, Path(tmp))
            svc.load()

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl: Table = db.table(VEHICLE_V3)
            root = Path(tmp)
            file_root = root / str(2019)
            file_root.mkdir()
            vehicle_shard_dao = Mock()
            vehicle_shard_dao.all.return_value = [VehicleShard.for_path(Path('2019/01-01.json')),
                                                  VehicleShard.for_path(Path('2019/01-02.json'))]

            svc = VehicleShardLoader(tbl, vehicle_shard_dao, root)

            with TinyDB(file_root / '01-01.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                tbl_shard.insert_multiple([{'id': '1'}, {'id': '2'}])

            with TinyDB(file_root / '01-02.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                tbl_shard.insert_multiple([{'id': '3'}, {'id': '4'}])

            svc.load()

            self.assertEqual(4, len(tbl))
            docs = tbl.all()
            self.assertIn({'id': '1'}, docs)
            self.assertIn({'id': '2'}, docs)
            self.assertIn({'id': '3'}, docs)
            self.assertIn({'id': '4'}, docs)
            vehicle_shard_dao.all.assert_called_once_with()

    def test_close_zero(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl = db.table(VEHICLE_V3)
            svc = VehicleShardLoader(tbl, Mock(), Path(tmp))
            svc.close()

    def test_close(self):
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl: Table = db.table(VEHICLE_V3)
            root = Path(tmp) / VEHICLE_V3

            ts = 0
            ts2 = 86400

            vehicle_shard_dao = Mock()
            svc = VehicleShardLoader(tbl, vehicle_shard_dao, root)

            tbl.insert_multiple([
                {'id': '1', 'first_spotted': ts, 'last_spotted': ts2},
                {'id': '2', 'first_spotted': ts, 'last_spotted': ts2},
                {'id': '3', 'first_spotted': ts2, 'last_spotted': ts2},
                {'id': '4', 'first_spotted': ts2, 'last_spotted': ts2}
            ])

            svc.close()

            with TinyDB(root / '1970' / '01-01.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                docs = tbl_shard.all()
                self.assertEqual(2, len(docs))
                self.assertIn({'id': '1', 'first_spotted': ts, 'last_spotted': ts2}, docs)
                self.assertIn({'id': '2', 'first_spotted': ts, 'last_spotted': ts2}, docs)

            with TinyDB(root / '1970' / '01-02.json') as db_shard:
                tbl_shard: Table = db_shard.table(VEHICLE_V3)
                docs = tbl_shard.all()
                self.assertEqual(2, len(docs))
                self.assertIn({'id': '3', 'first_spotted': ts2, 'last_spotted': ts2}, docs)
                self.assertIn({'id': '4', 'first_spotted': ts2, 'last_spotted': ts2}, docs)

            assert [call(VehicleShard.for_path(Path('1970/01-01.json'))),
                    call(VehicleShard.for_path(Path('1970/01-02.json')))] == vehicle_shard_dao.add.mock_calls

    def test_shard_removed_on_close(self):
        ts = 0
        ts2 = 86400
        with tempfile.TemporaryDirectory() as tmp, TinyDB(storage=MemoryStorage) as db:
            tbl: Table = db.table(VEHICLE_V3)
            tbl.insert_multiple([
                {'id': '1', 'first_spotted': ts, 'last_spotted': ts},
                {'id': '2', 'first_spotted': ts, 'last_spotted': ts},
                {'id': '3', 'first_spotted': ts2, 'last_spotted': ts2},
                {'id': '4', 'first_spotted': ts2, 'last_spotted': ts2}
            ])

            vehicle_shard_dao = Mock()
            svc = VehicleShardLoader(tbl, vehicle_shard_dao, Path(tmp))
            svc.close()

            vehicle_shard_dao.remove.assert_called_once_with(VehicleShard.for_path(Path('1970/01-01.json')))
