import typing

import tinydb
from tinydb import TinyDB, Query


class FilterDao:
    def __init__(self, db: TinyDB):
        self._tbl: tinydb.database.Table = db.table('filter')

    def insert_multiple(self, data: list) -> typing.List[int]:
        return self._tbl.insert_multiple(data)

    def insert(self, data) -> int:
        return self._tbl.insert(data)

    def get(self, cat_id, name) -> dict:
        params = Query()
        return self._tbl.get(params.name == name)

    def get_required(self, cat_id, name) -> dict:
        result = self.get(cat_id, name)
        if result is None:
            raise ValueError('Not found', cat_id, name)
        else:
            return result

    def names_to_keys(self, category_id: str, param_name, param_value=None) -> typing.Tuple[str, str]:
        param_obj = self.get_required(category_id, param_name)
        param_type = param_obj['type']
        if param_type == 'NUMERIC':
            raise NotImplementedError
        if param_type != 'MULTI' and param_type != 'SINGLE':
            return param_obj['id'], param_value

        if param_value is None:
            raise ValueError('Missing parameter param_value', param_type)
        value_objects = [p['value'] for p in param_obj['values'] if p['name'] == param_value]
        if len(value_objects) == 1:
            return param_obj['id'], value_objects[0]
        else:
            raise ValueError("Didn't find single value", value_objects)

    def purge(self):
        self._tbl.purge()
