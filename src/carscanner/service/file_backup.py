import logging
import pathlib

import tinydb

from carscanner.dao import CarOfferDao
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from carscanner.data import VehicleShardLoader
from carscanner.service.backup import BackupService
from carscanner.utils import datetime_to_unix

log = logging.getLogger(__name__)


class FileBackupService(BackupService):
    def __init__(self, dao: CarOfferDao, vehicle_path_v3: pathlib.Path):
        self._dao = dao
        self._vehicle_path_v3 = vehicle_path_v3

    def backup(self):
        log.info('Preparing backup')
        with tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as db:
            tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
            tbl.insert_multiple(BackupService._convert(obj) for obj in self._dao.all())

            VehicleShardLoader(tbl, self._vehicle_path_v3).close()


if __name__ == '__main__':
    from carscanner.cli.cmd import CmdContext, ENV_LOCAL
    import argparse
    import pathlib
    import carscanner.utils

    carscanner.utils.configure_logging()

    ns = argparse.Namespace
    ns.environment = ENV_LOCAL
    ns.no_fetch = False
    ns.data = pathlib.Path('~/projects/carscanner-data/').expanduser()
    ctx = CmdContext(ns)

    ctx.backup_service().backup()
