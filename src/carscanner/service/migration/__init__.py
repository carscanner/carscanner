import logging
import typing

import tinydb
from tinydb import Query
from tinydb.database import Table

from carscanner.dao import MetadataDao
from .v2 import MigrationV2
from .v3 import MigrationV3

_VERSION = 'version'

log = logging.getLogger(__name__)


class MigrationService:
    def __init__(self, cars_db_v1: tinydb.TinyDB, v2migration: typing.Callable,
                 v3migration: typing.Callable):
        self._cars_db_v1 = cars_db_v1
        self._v2 = v2migration
        self._v3 = v3migration

    def check_migrate(self):
        from carscanner.dao.meta import META_V2

        meta_tbl_v1: Table = self._cars_db_v1.table()

        if not len(meta_tbl_v1) and META_V2 not in self._cars_db_v1.tables():
            log.info("No metadata detected")
            return

        if len(meta_tbl_v1):
            raw_meta = meta_tbl_v1.get(Query())
            assert raw_meta and _VERSION not in raw_meta.keys()

            # default table in use - version 1
            log.info("Migrate data to version 2")
            self._v2().migrate()

        if META_V2 in self._cars_db_v1.tables():
            meta_tbl: Table = self._cars_db_v1.table(META_V2)
            raw_meta = meta_tbl.get(Query())
            assert raw_meta and raw_meta[_VERSION] <= MetadataDao.META_VER

            if raw_meta[_VERSION] == 2:
                log.info("Migrate data to version 3")
                self._v3().migrate()
