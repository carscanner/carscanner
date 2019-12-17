import dataclasses
import pathlib

import tinydb


@dataclasses.dataclass(frozen=True)
class VehicleShard:
    path: pathlib.Path

    @staticmethod
    def from_dict(d: dict):
        return VehicleShard.for_path(d['path'])

    def to_dict(self):
        return {'path': str(self.path)}

    @staticmethod
    def for_path(path: pathlib.Path):
        return VehicleShard(path)


class VehicleShardDao:
    def __init__(self, table: tinydb.database.Table):
        self._table = table

    def all(self):
        return [VehicleShard.from_dict(doc) for doc in self._table.all()]

    def add(self, shard: VehicleShard):
        self._table.upsert(shard.to_dict(), tinydb.Query().path == str(shard.path))

    def remove(self, shard: VehicleShard):
        self._table.remove(tinydb.Query().path == shard.path)
