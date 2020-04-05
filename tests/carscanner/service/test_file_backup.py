import datetime
import decimal
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from carscanner.dao import CarOffer
from carscanner.service import FileBackupService
from carscanner.utils import datetime_to_unix


class TestFileBackupService(TestCase):
    @patch('carscanner.service.file_backup.VehicleShardLoader')
    def test_backup(self, vsl_mock):
        car_offer_dao = Mock()
        car_offer_dao.all = Mock(return_value=[])
        export_path = Mock()
        export_svc = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            svc = FileBackupService(car_offer_dao, export_path, export_svc, temp)
            svc.backup()

        vsl_mock.assert_called_once()
        vsl_mock().close.assert_called_once_with()

    def test__convert(self):
        car_offer_dao = Mock()
        car_offer_dao.all = Mock(return_value=[])
        export_path = Mock()
        export_svc = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            svc = FileBackupService(car_offer_dao, export_path, export_svc, temp)
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
