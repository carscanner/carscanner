import decimal
import logging
import pathlib
import typing
from datetime import datetime

import bson
import pymongo.database
import pymongo.errors
import tinydb

import carscanner.dao
import carscanner.data
from carscanner import utils
from carscanner.utils import memoized
from carscanner.dao.meta import META_V2 as _META_V3
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3

log = logging.getLogger(__name__)


class MetadataVersionException(BaseException):
    pass


class MigrationService:
    def __init__(self,
                 vehicle_path_v1: pathlib.Path,
                 vehicle_path_v3: pathlib.Path,
                 vehicle_tbl_v3_factory: typing.Callable[[], tinydb.database.Table],
                 db_v4: pymongo.database.Database
                 ):
        self._vehicle_path_v1 = vehicle_path_v1
        self._vehicle_path_v3 = vehicle_path_v3
        self._vehicle_tbl_v3_factory = vehicle_tbl_v3_factory
        self._db_v4 = db_v4

    def check_migrate(self):
        if self.is_current_version():
            if self.is_previous_version():
                raise MetadataVersionException('Found both previous and current versions of metadata')
        elif self.is_previous_version():
            self.do_migrate()

    def is_previous_version(self) -> bool:
        # The previous version was the last one to use tinydb
        # there may be either no data or the previous version
        if not self._vehicle_path_v1.is_file():
            return False
        with tinydb.TinyDB(self._vehicle_path_v1, storage=carscanner.data.ReadOnlyMiddleware()) as db:
            version = db.table('meta').get(tinydb.Query())['version']
            assert 3 == version, "Cannot migrate from older version"
            return True

    def is_current_version(self) -> bool:
        # this is the first version to use MongoDB
        # there mey be either no data or it's the current version

        if 'meta' not in self._db_v4.list_collection_names():
            return False
        assert 4 == self._meta_col().find_one({})['version']
        return True

    def do_migrate(self) -> None:
        self.migrate_data()
        self.migrate_meta()

        self._vehicle_path_v1.unlink()

    def migrate_data(self):
        self._vehicle_col().create_index([
            ('_id.id', pymongo.ASCENDING),
            ('year', pymongo.ASCENDING),
            ('mileage', pymongo.ASCENDING),
        ], name='search_export')
        try:
            self._vehicle_col().insert_many(
                (convert(doc) for doc in self._vehicle_tbl_v3_factory().all()),
                False
            )
        except pymongo.errors.BulkWriteError as e:
            print(e.code)
            raise

    def migrate_meta(self):
        with tinydb.TinyDB(self._vehicle_path_v1, middleware=carscanner.data.ReadOnlyMiddleware()) as db_v3:
            tbl: tinydb.database.Table = db_v3.table('meta')
            raw_meta = tbl.get(tinydb.Query())
        raw_meta['timestamp'] = datetime.fromisoformat(raw_meta['timestamp'])
        raw_meta['version'] = carscanner.dao.meta.MetadataDao.META_VER

        self._meta_col().update_one({}, {'$set': raw_meta}, True)

    @memoized
    def _meta_col(self):
        return self._db_v4.get_collection(_META_V3, codec_options=self._db_v4.codec_options)

    @memoized
    def _vehicle_col(self):
        return self._db_v4.get_collection(_VEHICLE_V3, codec_options=self._db_v4.codec_options)


def convert(doc: dict) -> dict:
    result = doc.copy()
    result['_id'] = {'provider': 'allegro', 'id': doc['id']}
    del result['id']

    result['first_spotted'] = utils.unix_to_datetime(result['first_spotted'])
    result['last_spotted'] = utils.unix_to_datetime(result['last_spotted'])

    price = decimal.Decimal(doc['price']).quantize(decimal.Decimal('0.01'))
    result['price'] = bson.Decimal128(price)

    return result


if __name__ == '__main__':
    from carscanner.cmd import Context, ENV_LOCAL
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
