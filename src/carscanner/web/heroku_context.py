import os
import pathlib

import carscanner.allegro
import carscanner.dao
from carscanner.context import Context
from carscanner.service import GitBackupService
from carscanner.utils import memoized


class HerokuContext(Context):
    def __init__(self):
        super().__init__()

    @memoized
    def allegro_auth(self):
        ts = carscanner.dao.MongoTrustStore(self.token_collection())
        cs = carscanner.allegro.EnvironClientCodeStore()
        return carscanner.allegro.CarScannerCodeAuth(cs, ts, False)

    @property
    def backup_remote(self):
        return os.environ['BACKUP_REMOTE']

    @memoized
    def backup_service(self):
        return GitBackupService(self.car_offer_dao(), self.data_path, self.backup_remote)

    @property
    def data_path(self):
        return pathlib.Path(os.environ['DATA_PATH']).expanduser()
