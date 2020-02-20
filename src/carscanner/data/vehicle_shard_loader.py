import datetime
import logging
import pathlib

import tinydb

from carscanner import utils
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from .readonly import ReadOnlyMiddleware

log = logging.getLogger(__name__)


class VehicleShardLoader:
    def __init__(self, vehicle_tbl: tinydb.database.Table, data_root: pathlib.Path):
        self._vehicle_tbl = vehicle_tbl
        self._data_root = data_root

    def load(self) -> None:
        def load_file(path: pathlib.Path) -> None:
            log.debug("load %s", path)
            with tinydb.TinyDB(path, storage=ReadOnlyMiddleware(tinydb.storages.JSONStorage)) as db:
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                self._vehicle_tbl.insert_multiple(tbl.all())

        utils.walk_path(self._data_root, load_file)

    def close(self) -> None:
        log.info("Saving as shards")
        shards = {}
        all_data = sorted(self._vehicle_tbl.all(), key=lambda i: (i['first_spotted'], i['id']))
        for doc in all_data:
            shard = VehicleShardLoader._shard_value(doc)
            shards.setdefault(shard, []).append(doc)

        for shard_val, data in sorted(shards.items(), key=lambda t: t[0]):
            path = VehicleShardLoader._path_for_shard(shard_val)
            log.debug("save %s", path)

            path_full = self._data_root / path
            path_full.parent.mkdir(parents=True, exist_ok=True)

            with tinydb.TinyDB(path_full, indent=2) as db:
                db.purge_table(_VEHICLE_V3)
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                tbl.insert_multiple(data)

    @staticmethod
    def _shard_value(doc: tinydb.database.Document) -> datetime.date:
        return utils.unix_to_datetime(doc['first_spotted']).date()

    @staticmethod
    def _path_for_shard(shard_date: datetime.date) -> pathlib.Path:
        return pathlib.Path(str(shard_date.year)) / f'{shard_date.month:02}-{shard_date.day:02}.json'
