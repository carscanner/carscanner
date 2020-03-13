import logging

import pymongo.database
import pymongo.errors

from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from carscanner.dao.meta import META_V2 as _META_V2, META_VER as _META_VER
from carscanner.utils import memoized

log = logging.getLogger(__name__)


class MetadataVersionException(BaseException):
    pass


class MigrationService:
    def __init__(self,
                 db_v4: pymongo.database.Database,
                 ):
        self._db_v4 = db_v4

    def check_migrate(self):
        if self.is_current_version():
            log.info("Database in the current version")
            if self.is_previous_version():
                raise MetadataVersionException('Found both previous and current versions of metadata')
        elif self.is_previous_version():
            log.info("Database in the previous version")
            self.do_migrate()

    def is_previous_version(self) -> bool:
        return self._meta_col().count_documents({'version': 4}) == 1

    def is_current_version(self) -> bool:
        return self._meta_col().count_documents({'version': _META_VER}) == 1

    def do_migrate(self) -> None:
        self.migrate_data()
        self.migrate_meta()

    def migrate_data(self):
        try:
            self._vehicle_col().update_many({}, {'$set': {'active': True}})
        except pymongo.errors.BulkWriteError as e:
            print(e.code)
            raise

    def migrate_meta(self):
        self._meta_col().update_one({}, {'$set': {'version': _META_VER}}, True)

    @memoized
    def _meta_col(self):
        return self._db_v4.get_collection(_META_V2, codec_options=self._db_v4.codec_options)

    @memoized
    def _vehicle_col(self):
        return self._db_v4.get_collection(_VEHICLE_V3, codec_options=self._db_v4.codec_options)


if __name__ == '__main__':
    from carscanner.cli.cmd import Context, ENV_LOCAL
    import argparse
    import pathlib
    import carscanner.utils

    carscanner.utils.configure_logging()

    ctx = Context()
    ctx.ns = argparse.Namespace
    ctx.ns.environment = ENV_LOCAL
    ctx.ns.no_fetch = False
    ctx.ns.data = pathlib.Path('~/projects/carscanner-data/').expanduser()

    ctx.migration_service().check_migrate()
