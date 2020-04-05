import datetime

from . import BackupService, FilterService, OfferService
from ..dao import MetadataDao


class VehicleUpdaterService:
    def __init__(self,
                 offers_svc: OfferService,
                 metadata_dao: MetadataDao,
                 filter_svc: FilterService,
                 datetime_now: datetime.datetime,
                 backup_svc: BackupService,
                 ):
        self._ts = datetime_now
        self._filter_svc = filter_svc
        self._meta_dao = metadata_dao
        self._offer_svc = offers_svc
        self._backup_service = backup_svc

    def update(self):
        self._meta_dao.report()
        self._filter_svc.load_filters()
        self._offer_svc.get_offers()
        self._meta_dao.update(self._ts)
        self._backup_service.backup()
