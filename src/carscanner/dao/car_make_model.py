import typing

from tinydb import TinyDB, where

_TABLE = 'make_model'


class CarMakeModelDao:
    def __init__(self, db: TinyDB):
        self._db = db
        self._tbl = db.table(_TABLE)

    def get_models_by_make(self, make: str) -> typing.List[str]:
        doc = self._tbl.get(where('make') == make.lower())
        return doc["models"] if doc else []

    def insert(self, make: dict) -> int:
        return self._tbl.insert(make)

    def purge(self):
        self._db.purge_table(_TABLE)
