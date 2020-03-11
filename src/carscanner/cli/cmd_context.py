import carscanner.allegro
import carscanner.dao
import carscanner.service
from carscanner.context import Context
from carscanner.utils import memoized

ENV_TRAVIS = 'travis'
ENV_LOCAL = 'local'


class CmdContext(Context):
    def __init__(self, ns):
        super().__init__()
        ns.data = ns.data.expanduser()
        self._ns = ns

    @memoized
    def allegro_auth(self):
        ts = carscanner.dao.MongoTrustStore(self.token_collection())
        if self.environment == ENV_LOCAL:
            cs = carscanner.allegro.YamlClientCodeStore(carscanner.allegro.codes_path)
            allow_fetch = not self.ns.no_fetch
        elif self.environment == ENV_TRAVIS:
            cs = carscanner.allegro.EnvironClientCodeStore()
            allow_fetch = False
        else:
            raise ValueError(self.environment)
        return carscanner.allegro.CarScannerCodeAuth(cs, ts, allow_fetch)

    @property
    def data_path(self):
        return self._ns.data

    @property
    def environment(self):
        return self._ns.environment

    @property
    def ns(self):
        return self._ns
