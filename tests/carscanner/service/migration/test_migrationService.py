from unittest import TestCase
from unittest.mock import Mock

from carscanner.service.migration import MigrationService
from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage


class TestMigrationService(TestCase):
    def test_check_migrate_zero(self):
        v2_mock = Mock()
        v3_mock = Mock()
        old_cars_db = TinyDB(storage=MemoryStorage)
        new_cars_db = TinyDB(storage=MemoryStorage)
        svc = MigrationService(old_cars_db, new_cars_db, v2_mock, v3_mock)

        svc.check_migrate()

    def test_check_migrate_from_v1(self):
        v2_mock = Mock()
        v3_mock = Mock()
        old_cars_db = TinyDB(storage=MemoryStorage)
        new_cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = old_cars_db.table()
        tbl.insert({'timestamp': 'timestamp', 'host': 'host'})
        svc = MigrationService(old_cars_db, new_cars_db, v2_mock, v3_mock)

        svc.check_migrate()

        v2_mock.migrate.assert_called_once()
        v3_mock.migrate.assert_not_called()

    def test_check_migrate_from_v4_in_default(self):
        v2_mock = Mock()
        v3_mock = Mock()
        cars_db_v1 = TinyDB(storage=MemoryStorage)
        cars_db_v3 = Mock
        tbl: Table = cars_db_v1.table()
        tbl.insert({'version': 4})
        svc = MigrationService(cars_db_v1, cars_db_v3, v2_mock, v3_mock)

        self.assertRaises(AssertionError, svc.check_migrate)

        v2_mock.migrate.assert_not_called()
        v3_mock.migrate.assert_not_called()

    def test_check_migrate_from_v2(self):
        v2_mock = Mock()
        v3_mock = Mock()
        old_cars_db = TinyDB(storage=MemoryStorage)
        new_cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = old_cars_db.table('meta')
        tbl.insert({'timestamp': 'timestamp', 'host': 'host', 'version': 2})
        svc = MigrationService(old_cars_db, new_cars_db, v2_mock, v3_mock)

        svc.check_migrate()

        v2_mock.migrate.assert_not_called()
        v3_mock.migrate.assert_called_once()

    def test_check_migrate_from_v3(self):
        v2_mock = Mock()
        v3_mock = Mock()
        old_cars_db = TinyDB(storage=MemoryStorage)
        new_cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = old_cars_db.table('meta')
        tbl.insert({'version': 3})
        svc = MigrationService(old_cars_db, new_cars_db, v2_mock, v3_mock)

        svc.check_migrate()

        v2_mock.migrate.assert_not_called()
        v3_mock.migrate.assert_not_called()

    def test_check_migrate_from_v4(self):
        v2_mock = Mock()
        v3_mock = Mock()
        old_cars_db = TinyDB(storage=MemoryStorage)
        new_cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = old_cars_db.table('meta')
        tbl.insert({'version': 4})
        svc = MigrationService(old_cars_db, new_cars_db, v2_mock, v3_mock)

        self.assertRaises(AssertionError, svc.check_migrate)

        v2_mock.migrate.assert_not_called()
        v3_mock.migrate.assert_not_called()
