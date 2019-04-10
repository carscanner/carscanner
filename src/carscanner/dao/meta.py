import datetime
import logging
import platform

from tinydb import TinyDB, Query
from tinydb.database import Table

log = logging.getLogger(__name__)


class MetadataDao:
    def __init__(self, db: TinyDB):
        self._db = db
        self._tbl: Table = db.table('meta')

        self._meta = self._tbl.get(Query())
        if self._meta:
            assert self._meta['version'] == 3

    def update(self, ts: datetime.datetime):
        self._meta['timestamp'] = ts.isoformat()
        self._meta['host'] = platform.node()
        self._tbl.upsert(self._meta, Query())

    def report(self):
        if self._meta:
            log.info('Last run at %s on %s', self._meta['timestamp'], self._meta['host'])
        else:
            log.info('First run')

    def migrate(self):
        old_tbl: Table = db.table(db.DEFAULT_TABLE)
        old_meta = old_tbl.get(Query())
        new_meta = self._tbl.get(Query())
        if new_meta:
            raise Exception('Already migrated')
        if not old_meta:
            raise Exception('No metadata to migrate')

        old_meta['version'] = 2

        self._tbl.insert(old_meta)
        old_tbl.purge()
        self._meta = old_meta


if __name__ == '__main__':
    from sys import argv

    path = argv[1]
    with TinyDB(path, indent=2) as db:
        meta = MetadataDao(db)
        meta.migrate()
        meta.report()
