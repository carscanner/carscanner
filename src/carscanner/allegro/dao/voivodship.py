from dataclasses import dataclass

import tinydb
from tinydb import where

from .base import BaseDao


# @dataclass
# class Voivodeship:
#     id: int = None
#     name: str = None
#
#     def load_dict(self, d: dict) -> None:
#         self.id = d['id']
#         self.name = d['name']


class VoivodeshipDao(BaseDao):
    def __init__(self, db: tinydb.TinyDB):
        super().__init__(db)
        self._tbl: tinydb.database.Table = db.table('voivodeship')
        self._q = tinydb.Query()

    def insert(self, data: dict) -> int:
        return self._tbl.insert(data)

    def get_name_by_id(self, id: int) -> str:
        return self._tbl.get(where('id') == id)['name']
