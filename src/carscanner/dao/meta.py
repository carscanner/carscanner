import dataclasses
import datetime
import logging
import platform
import typing

from tinydb import TinyDB, Query
from tinydb.database import Table

K_TS = 'timestamp'

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Metadata:
    host: str
    timestamp: str
    version: int

    @staticmethod
    def from_dict(d: dict) -> 'Metadata':
        return Metadata(**d)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class MetadataDao:
    META_VER: int = 2
    """Metadata file version expected by the software"""

    def __init__(self, db: TinyDB):
        self._db = db
        self._tbl: Table = db.table('meta')
        self._meta: typing.Optional[Metadata] = None

    def post_init(self):
        raw_meta = self._tbl.get(Query())
        self._meta = Metadata.from_dict(raw_meta) if raw_meta else MetadataDao._init_metadata()
        assert self._meta.version == MetadataDao.META_VER

    def update(self, ts: datetime.datetime):
        self._meta.timestamp = ts.isoformat()
        self._meta.host = platform.node()
        self._tbl.upsert(self._meta, Query())

    def report(self):
        if self._meta:
            log.info('Last run at %s on %s', self._meta.timestamp, self._meta.host)
        else:
            log.info('First run')

    def get_timestamp(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self._meta.timestamp).astimezone(datetime.timezone.utc)

    def _set_meta(self, _meta: Metadata) -> None:
        log.warning("External update of metadata")
        self._meta = _meta

    meta = property(fset=_set_meta)

    @staticmethod
    def _init_metadata() -> Metadata:
        return Metadata(platform.node(), None, MetadataDao.META_VER)
