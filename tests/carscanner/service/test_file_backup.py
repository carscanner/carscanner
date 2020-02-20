import datetime
import decimal
import tempfile
from pathlib import Path
from pprint import pprint
from unittest import TestCase, mock
from unittest.mock import patch, Mock
import carscanner.data
from carscanner.dao import CarOffer
from carscanner.service import FileBackupService
from carscanner.utils import datetime_to_unix


class TestFileBackupService(TestCase):
    @mock.patch('carscanner.service.file_backup.VehicleShardLoader')
    def test_backup(self, vsl_mock):
        car_offer_dao = Mock()
        car_offer_dao.all = Mock(return_value=[])
        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            svc = FileBackupService(car_offer_dao, temp)
            svc.backup()

        vsl_mock.assert_called_once()
        vsl_mock().close.assert_called_once_with()

    def test__convert(self):
        car_offer_dao = Mock()
        car_offer_dao.all = Mock(return_value=[])
        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            svc = FileBackupService(car_offer_dao, temp)
            ts = datetime.datetime.utcnow()
            d = svc._convert(CarOffer(ts, price=decimal.Decimal('1')))

            self.assertEqual({
                'first_spotted': datetime_to_unix(ts),
                'price': '1',
                'active': True,
                'fuel': None,
                'id': None,
                'image': None,
                'imported': None,
                'last_spotted': None,
                'location': None,
                'make': None,
                'mileage': None,
                'model': None,
                'name': None,
                'url': None,
                'voivodeship': None,
                'year': None
            }, d)
