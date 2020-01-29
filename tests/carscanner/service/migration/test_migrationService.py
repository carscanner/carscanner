import tempfile
from datetime import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from bson import Decimal128
from mongomock import MongoClient
from tinydb import TinyDB

from carscanner.service.migration import MigrationService


class TestMigrationService(TestCase):
    def test_check_migrate_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temprootpath = Path(tmpdir)
            svc = MigrationService(
                temprootpath / 'cars.json',
                temprootpath / 'vehicle', Mock(),
                self._db(),
            )
            svc.check_migrate()

    def test_check_migrate_from_previous(self):
        ts = datetime.utcnow()
        with tempfile.TemporaryDirectory() as tmpdir:
            temprootpath = Path(tmpdir)
            path_v1 = temprootpath / 'cars.json'
            with TinyDB(path_v1) as db_v1:
                db_v1.table('meta').insert({
                    'version': 3,
                    'timestamp': ts.isoformat(),
                    'host': 'host',
                })

            path_v3 = temprootpath / 'vehicle'
            path_v3_file = path_v3 / '2020' / '0101.json'
            path_v3_file.parent.mkdir(parents=True)
            with TinyDB(path_v3_file) as db_v3:
                db_v3.table('vehicle').insert({
                    "id": "7597123698",
                    "make": "Audi",
                    "model": "Q7",
                    "year": 2010,
                    "mileage": 89000,
                    "image": "image-url",
                    "url": "allegro-url",
                    "name": "my beloved car",
                    "price": "88500",
                    "first_spotted": 1554749924,
                    "last_spotted": 1554757581,
                    "voivodeship": "kujawsko-pomorskie",
                    "location": "Grudziądz",
                    "imported": False,
                })

                db = self._db()

                svc = MigrationService(
                    path_v1,
                    path_v3,
                    lambda: db_v3.table('vehicle'),
                    db,
                )

                svc.check_migrate()

                self.assertIn('meta', db.list_collection_names())
                meta_col = db.get_collection('meta')
                self.assertIs(1, meta_col.count_documents({}))

                meta_raw = meta_col.find_one({})
                self.assertEqual({
                    'version': 4,
                    'timestamp': ts.replace(microsecond=int(ts.microsecond / 1000) * 1000),
                    'host': 'host',
                }, {k: v for k, v in meta_raw.items() if k in ['timestamp', 'version', 'host']})

                self.assertIn('vehicle', db.list_collection_names())
                vehicle_col = db.get_collection('vehicle')
                self.assertIs(1, vehicle_col.count_documents({}))
                vehicle_raw = vehicle_col.find_one({})
                self.assertEqual({
                    'make': 'Audi',
                    'model': 'Q7',
                    'year': 2010,
                    'mileage': 89000,
                    'image': 'image-url',
                    'url': 'allegro-url',
                    'name': 'my beloved car',
                    'price': Decimal128('88500.00'),
                    'first_spotted': datetime(2019, 4, 8, 18, 58, 44),
                    'last_spotted': datetime(2019, 4, 8, 21, 6, 21),
                    'voivodeship': 'kujawsko-pomorskie',
                    'location': 'Grudziądz',
                    'imported': False,
                    '_id': {
                        'provider': 'allegro',
                        'id': '7597123698'
                    }
                },
                    vehicle_raw
                )

    def test_migrate_from_current_no_action(self):
        ts = datetime.utcnow()
        ts = ts.replace(microsecond=int(ts.microsecond / 1000) * 1000)
        db = self._db()
        db.meta.insert_one({
            'version': 4,
            'timestamp': ts,
            'host': 'host',
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            temprootpath = Path(tmpdir)
            svc = MigrationService(
                temprootpath / 'cars.json',
                temprootpath / 'vehicle',
                Mock(),
                db,
            )
            svc.check_migrate()

    def _db(self):
        return MongoClient('mongodb://fakehost/mockdb', tz_aware=True).get_database()
