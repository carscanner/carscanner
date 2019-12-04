import pathlib

import tinydb
from tinydb import Query
from tinydb.database import Table

from carscanner.dao.car_offer import VEHICLE_V1 as _VEHICLE_V1, VEHICLE_V3 as _VEHICLE_V3
from carscanner.dao.meta import META_V2 as _META_V2, Metadata


class MigrationV3:
    def __init__(self, vehicle_db_v1: tinydb.TinyDB, vehicle_db_v3: tinydb.TinyDB, data_root: pathlib.Path):
        self._vehicle_db_v1 = vehicle_db_v1
        self._vehicle_db_v3 = vehicle_db_v3
        self._data_root = data_root

    def migrate(self):
        meta_tbl: Table = self._vehicle_db_v1.table(_META_V2)
        meta = Metadata(**meta_tbl.get(Query()))
        assert meta.version is 2

        vehicle_tbl_v2: Table = self._vehicle_db_v1.table(_VEHICLE_V1)
        vehicle_tbl_v3: Table = self._vehicle_db_v3.table(_VEHICLE_V3)
        vehicle_tbl_v3.insert_multiple(vehicle_tbl_v2.all())
        self._vehicle_db_v1.purge_table(_VEHICLE_V1)

        meta_tbl.update({'version': 3}, Query())
