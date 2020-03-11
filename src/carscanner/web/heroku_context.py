import pathlib

import carscanner.allegro
import carscanner.dao
from carscanner.context import Context
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
    def data_path(self):
        import os
        return pathlib.Path(os.environ['DATA_PATH']).expanduser()

