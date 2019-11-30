from unittest import TestCase
from unittest.mock import Mock

from carscanner.service.migration import MigrationService
from tinydb import TinyDB
from tinydb.database import Table
from tinydb.storages import MemoryStorage


class TestMigrationService(TestCase):
    def test_check_migrate_zero(self):
        v2_mock = Mock()
        cars_db = TinyDB(storage=MemoryStorage)
        svc = MigrationService(cars_db, v2_mock)

        svc.check_migrate()

    def test_check_migrate_from_v1(self):
        v2_mock = Mock()
        cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = cars_db.table()
        tbl.insert({'timestamp': 'timestamp', 'host': 'host'})
        svc = MigrationService(cars_db, v2_mock)

        svc.check_migrate()

        v2_mock.migrate.assert_called_once()

    def test_check_migrate_from_v2(self):
        v2_mock = Mock()
        cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = cars_db.table('meta')
        tbl.insert({'timestamp': 'timestamp', 'host': 'host', 'version': 2})
        svc = MigrationService(cars_db, v2_mock)

        svc.check_migrate()

        v2_mock.migrate.assert_not_called()

    def test_check_migrate_from_v3(self):
        v2_mock = Mock()
        cars_db = TinyDB(storage=MemoryStorage)
        tbl: Table = cars_db.table('meta')
        tbl.insert({'version': 3})
        svc = MigrationService(cars_db, v2_mock)

        self.assertRaises(AssertionError, svc.check_migrate)

        v2_mock.migrate.assert_not_called()
