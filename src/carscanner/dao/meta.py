import datetime
import logging
import platform

from tinydb import TinyDB, Query
from tinydb.database import Table

K_TS = 'timestamp'

log = logging.getLogger(__name__)


class MetadataDao:
    _meta_version = 2

    def __init__(self, db: TinyDB):
        self._db = db
        self._tbl: Table = db.table('meta')

        self._meta = self._tbl.get(Query())
        if self._meta:
            assert self._meta['version'] == MetadataDao._meta_version

    def update(self, ts: datetime.datetime):
        self._meta[K_TS] = ts.isoformat()
        self._meta['host'] = platform.node()
        self._tbl.upsert(self._meta, Query())

    def report(self):
        if self._meta:
            log.info('Last run at %s on %s', self._meta[K_TS], self._meta['host'])
        else:
            log.info('First run')

    def migrate(self):
        q = Query()
        old_tbl: Table = db.table(db.DEFAULT_TABLE)
        old_meta = old_tbl.get(q)
        new_meta = self._tbl.get(q)
        if new_meta:
            raise Exception('Already migrated')
        if not old_meta:
            raise Exception('No metadata to migrate')

        old_meta['version'] = MetadataDao._meta_version

        self._tbl.insert(old_meta)
        old_tbl.purge()
        self._meta = old_meta

    def get_timestamp(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self._meta[K_TS]).astimezone(datetime.timezone.utc)


if __name__ == '__main__':
    from sys import argv

    path = argv[1]
    with TinyDB(path, indent=2) as db:
        meta = MetadataDao(db)
        meta.migrate()
        meta.report()
