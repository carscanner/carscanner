from carscanner.dao import MetadataDao
from carscanner.dao.meta import Metadata
from tinydb import TinyDB, Query
from tinydb.database import Table


class MigrationV2:
    _VERSION = 2

    def __init__(self, meta_db: TinyDB, meta_dao: MetadataDao):
        self._metaDao = meta_dao
        self._db = meta_db

    def migrate(self):
        new_tbl: Table = self._db.table('meta')
        q = Query()
        old_tbl: Table = self._db.table()
        old_meta = old_tbl.get(q)
        new_meta = new_tbl.get(q)
        if new_meta:
            raise Exception('Already migrated')
        if not old_meta:
            raise Exception('No metadata to migrate')

        new_meta = Metadata(old_meta['host'], old_meta['timestamp'], MigrationV2._VERSION)

        new_tbl.insert(new_meta.to_dict())
        old_tbl.purge()
        self._metaDao.meta = new_meta
