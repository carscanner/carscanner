import typing

import tinydb


class VoivodeshipDao:
    def __init__(self, db: tinydb.TinyDB):
        self._tbl: tinydb.database.Table = db.table('voivodeship')
        self._q = tinydb.Query()

    def insert_multiple(self, data: typing.List[dict]) -> typing.List[int]:
        return self._tbl.insert_multiple(data)

    def get_name_by_id(self, id: int) -> str:
        return self._tbl.get(tinydb.Query().id == id)['name']
