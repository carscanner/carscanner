from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, PropertyMock

from bson import Decimal128
from mongomock import MongoClient, Collection, Database

from carscanner.dao.meta import META_VER
from carscanner.service.migration import MigrationService


class TestMigrationService(TestCase):
    def test_check_migrate_zero(self):
        db = self._db()
        svc = MigrationService(
            db,
        )
        svc.check_migrate()

    def test_check_migrate_from_previous(self):
        ts = datetime.utcnow().replace(microsecond=0)
        db = self._db()
        meta_col: Collection = db.meta
        meta_col.insert_one({
            'version': 4,
            'timestamp': ts,
            'host': 'host',
        })

        vehicle_col: Collection = db.vehicle
        vehicle_col.insert_one({
            '_id': {
                'provider': 'allegro',
                'id': 7597123698  # make up your mind, int or string
            },
            'first_spotted': ts,
            'fuel': 'Diesel',
            'image': 'image-url',
            'imported': False,
            'last_spotted': ts,
            'location': 'Grudziądz',
            'make': 'Audi',
            'mileage': 89000,
            'model': 'Q7',
            'name': 'my beloved car',
            'price': Decimal128('88500.00'),
            'url': 'allegro-url',
            'voivodeship': 'kujawsko-pomorskie',
            'year': 2010,
        })

        svc = MigrationService(
            db,
        )

        svc.check_migrate()

        self.assertEqual(META_VER, meta_col.find_one({})['version'])

        self.assertIs(1, vehicle_col.count_documents({}))
        vehicle_raw = vehicle_col.find_one({})
        self.assertEqual({
            '_id': {
                'provider': 'allegro',
                'id': 7597123698  # make up your mind, int or string
            },
            'active': True,
            'first_spotted': ts,
            'fuel': 'Diesel',
            'image': 'image-url',
            'imported': False,
            'last_spotted': ts,
            'location': 'Grudziądz',
            'make': 'Audi',
            'mileage': 89000,
            'model': 'Q7',
            'name': 'my beloved car',
            'price': Decimal128('88500.00'),
            'url': 'allegro-url',
            'voivodeship': 'kujawsko-pomorskie',
            'year': 2010,
        },
            vehicle_raw
        )

    def test_migrate_from_current_no_action(self):
        db = Mock()
        db.meta.count_documents = Mock(return_value=1)
        db.vehicle = PropertyMock()

        svc = MigrationService(
            db,
        )
        svc.check_migrate()

        db.vehicle.assert_not_called()

    def _db(self) -> Database:
        return MongoClient('mongodb://fakehost/mockdb').get_database()
