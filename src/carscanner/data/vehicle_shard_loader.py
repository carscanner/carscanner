import datetime
import logging
import pathlib

import tinydb

from carscanner import utils
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from .readonly import ReadOnlyMiddleware

log = logging.getLogger(__name__)

_SHARD_KEY = 'first_spotted'


class VehicleShardLoader:
    def __init__(self, vehicle_tbl: tinydb.database.Table, data_root: pathlib.Path):
        self._vehicle_tbl = vehicle_tbl
        self._data_root = data_root

    def load(self) -> None:
        def load_file(path: pathlib.Path) -> None:
            log.debug("load %s", path)
            with tinydb.TinyDB(path, storage=ReadOnlyMiddleware(tinydb.storages.JSONStorage)) as db:
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                self._vehicle_tbl.insert_multiple(sorted(tbl.all(), key=lambda doc: doc['id']))

        utils.walk_path(self._data_root, load_file)

    def close(self) -> None:
        shards = {}
        for doc in self._vehicle_tbl.all():
            shard = doc[_SHARD_KEY]
            shards.setdefault(shard, []).append(doc)

        for shard, data in shards.items():
            shard_date = datetime.date.fromtimestamp(shard)
            parent_dir = self._data_root / str(shard_date.year)
            parent_dir.mkdir(parents=True, exist_ok=True)
            path = parent_dir / f'{shard_date.month:02}-{shard_date.day:02}.json'

            log.debug("save %s", path)

            with tinydb.TinyDB(path, indent=2) as db:
                tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
                tbl.insert_multiple(data)
