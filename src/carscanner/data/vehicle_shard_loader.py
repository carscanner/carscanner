import datetime
import itertools
import logging
import pathlib

import tinydb

from carscanner import utils
from carscanner.dao import VehicleShard, VehicleShardDao
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from .readonly import ReadOnlyMiddleware

log = logging.getLogger(__name__)


class VehicleShardLoader:
    def __init__(self, vehicle_tbl: tinydb.database.Table, vehicle_shard_dao: VehicleShardDao, data_root: pathlib.Path):
        self._vehicle_tbl = vehicle_tbl
        self._vehicle_shard_dao = vehicle_shard_dao
        self._data_root = data_root

    def load(self) -> None:
        for shard in self._vehicle_shard_dao.all():
            log.debug("load %s", shard.path)
            with tinydb.TinyDB(self._data_root / shard.path, storage=ReadOnlyMiddleware()) as db:
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                self._vehicle_tbl.insert_multiple(tbl.all())

    def close(self) -> None:
        shards = {}
        timestamps = []
        all_data = sorted(self._vehicle_tbl.all(), key=lambda i: i['id'])
        for doc in all_data:
            shard = VehicleShardLoader._shard_value(doc)
            shards.setdefault(shard, []).append(doc)
            timestamps.append(doc['last_spotted'])

        last_timestamp = max(itertools.chain([0], timestamps))
        log.debug('Max timestamp: %i', last_timestamp)

        for shard_val, data in sorted(shards.items(), key=lambda t: t[0]):
            path = VehicleShardLoader._path_for_shard(shard_val)
            log.debug("save %s", path)

            path_full = self._data_root / path
            path_full.parent.mkdir(parents=True, exist_ok=True)

            with tinydb.TinyDB(path_full, indent=2) as db, \
                    tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as mem_db:

                db.purge_table(_VEHICLE_V3)
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                tbl.insert_multiple(data)

                mem_tbl: tinydb.database.Table = mem_db.table(_VEHICLE_V3)
                mem_tbl.insert_multiple(data)
                vehicle_shard = VehicleShard.for_path(path)
                if VehicleShardLoader._is_active(mem_tbl, last_timestamp):
                    self._vehicle_shard_dao.add(vehicle_shard)
                else:
                    self._vehicle_shard_dao.remove(vehicle_shard)

    @staticmethod
    def _shard_value(doc: tinydb.database.Document) -> datetime.date:
        return utils.unix_to_datetime(doc['first_spotted']).date()

    @staticmethod
    def _path_for_shard(shard_date: datetime.date) -> pathlib.Path:
        return pathlib.Path(str(shard_date.year)) / f'{shard_date.month:02}-{shard_date.day:02}.json'

    @staticmethod
    def _is_active(tbl: tinydb.database.Table, timestamp: int) -> bool:
        return tbl.count(tinydb.Query().last_spotted == timestamp) > 0
