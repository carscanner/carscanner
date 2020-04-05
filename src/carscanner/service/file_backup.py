import logging
import pathlib

import tinydb

from carscanner.dao import CarOfferDao
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from carscanner.data import VehicleShardLoader
from carscanner.service import BackupService, ExportService

log = logging.getLogger(__name__)


class FileBackupService(BackupService):
    def __init__(
            self,
            car_offer_dao: CarOfferDao,
            export_path: pathlib.Path,
            offer_export_svc: ExportService,
            vehicle_data_path_v3: pathlib.Path,
    ):
        self._car_offer_dao = car_offer_dao
        self._export_path = export_path
        self._offer_export_svc = offer_export_svc
        self._vehicle_data_path = vehicle_data_path_v3

    def backup(self):
        log.info('Preparing backup')
        with tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as db:

            tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
            tbl.insert_multiple(BackupService._convert(obj) for obj in self._car_offer_dao.all())

            self._offer_export_svc.export(self._export_path)
            VehicleShardLoader(tbl, self._vehicle_data_path).close()
        log.info('Backup done')
