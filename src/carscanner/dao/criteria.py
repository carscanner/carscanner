import typing
from dataclasses import dataclass

import tinydb

KEY_CATEGORY_ID = 'category_id'


@dataclass
class Criteria:
    category_id: str


class CriteriaDao:
    def __init__(self, db: tinydb.TinyDB):
        self._tbl: tinydb.database.Table = db.table('criteria')

    def insert_multiple(self, criteria: typing.List[Criteria]) -> int:
        return self._tbl.insert_multiple([crit.__dict__ for crit in criteria])

    def all(self) -> typing.List[Criteria]:
        return [Criteria(i[KEY_CATEGORY_ID]) for i in self._tbl.all()]

    def purge(self):
        self._tbl.purge()
