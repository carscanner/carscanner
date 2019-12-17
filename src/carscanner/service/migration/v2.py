from tinydb import TinyDB, Query
from tinydb.database import Table

from carscanner.dao.meta import META_V2 as _META_V2


class MigrationV2:
    def __init__(self, meta_db: TinyDB):
        self._db = meta_db

    def migrate(self):
        meta_tbl_v2: Table = self._db.table(_META_V2)
        q = Query()
        meta_tbl_v1: Table = self._db.table()
        meta_v1 = meta_tbl_v1.get(q)
        meta_v2 = meta_tbl_v2.get(q)
        if meta_v2:
            raise Exception('Already migrated')
        if not meta_v1:
            raise Exception('No metadata to migrate')

        meta_v2 = meta_v1.copy()
        meta_v2['version'] = _VERSION = 2

        meta_tbl_v2.insert(meta_v2)
        self._db.purge_table(self._db.DEFAULT_TABLE)
