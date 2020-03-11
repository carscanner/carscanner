import datetime
import pathlib
from concurrent import futures

import carscanner.dao
from . import FilterService, ExportService, FileBackupService, OfferService


class VehicleUpdaterService:
    def __init__(self,
                 offer_svc:OfferService,
                 meta_dao: carscanner.dao.MetadataDao,
                 filter_svc: FilterService,
                 export_svc: ExportService,
                 ts: datetime.datetime,
                 data_path: pathlib.Path,
                 backup_svc: FileBackupService,
                 executor: futures.Executor,
                 ):
        self.ts = ts
        self._filter_svc = filter_svc
        self._meta_dao = meta_dao
        self._offer_svc = offer_svc
        self._export_svc = export_svc
        self._data_path = data_path
        self._backup_service = backup_svc
        self._executor = executor
        self._output_path = data_path / 'export.json'

    def update(self):
        self._meta_dao.report()
        self._filter_svc.load_filters()
        self._offer_svc.get_offers()
        self._meta_dao.update(self.ts)
        self._executor.submit(self._export_svc.export, self._output_path)
        self._executor.submit(self._backup_service.backup)
