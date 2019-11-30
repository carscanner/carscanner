import logging

import tinydb
from carscanner.dao import MetadataDao
from tinydb import Query
from tinydb.database import Table

from .v2 import MigrationV2

log = logging.getLogger(__name__)


class MigrationService:
    def __init__(self, cars_db: tinydb.TinyDB, v2migration: MigrationV2):
        self._cars_db = cars_db
        self._v2 = v2migration

    def check_migrate(self):
        default_table: Table = self._cars_db.table()
        tables = self._cars_db.tables()

        if len(default_table):
            # default table in use - version 1
            log.info("Migrate data to version 2")
            self._v2.migrate()
        elif 'meta' in tables:
            meta_tbl: Table = self._cars_db.table('meta')
            raw_meta = meta_tbl.get(Query())
            if not raw_meta:
                log.info("No metadata detected")
                return
            else:
                assert raw_meta['version'] <= MetadataDao.META_VER
