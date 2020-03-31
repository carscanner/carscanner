import datetime
import pathlib
from concurrent import futures

from . import BackupService, ExportService, FilterService, OfferService
from ..dao import MetadataDao


class VehicleUpdaterService:
    def __init__(self,
                 offers_svc: OfferService,
                 metadata_dao: MetadataDao,
                 filter_svc: FilterService,
                 offer_export_svc: ExportService,
                 datetime_now: datetime.datetime,
                 backup_svc: BackupService,
                 executor: futures.Executor,
                 data_path: pathlib.Path,
                 export_path: pathlib.Path,
                 ):
        self.ts = datetime_now
        self._filter_svc = filter_svc
        self._meta_dao = metadata_dao
        self._offer_svc = offers_svc
        self._export_svc = offer_export_svc
        self._data_path = data_path
        self._backup_service = backup_svc
        self._executor = executor
        self._output_path = export_path

    def update(self):
        self._meta_dao.report()
        self._filter_svc.load_filters()
        self._offer_svc.get_offers()
        self._meta_dao.update(self.ts)
        self._executor.submit(self._export_svc.export, self._output_path)
        self._executor.submit(self._backup_service.backup)
