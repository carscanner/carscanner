import pathlib

import tinydb

from .readonly import ReadOnlyMiddleware


class DataManager:
    def __init__(self, data_dir: pathlib.Path):
        self._static_data_path = data_dir / 'static.json'
        self._cars_data_path = data_dir / 'cars.json'
        self._static: tinydb.TinyDB = None
        self._cars: tinydb.TinyDB = None
        self._mem: tinydb.TinyDB = None

    def static_data(self) -> tinydb.TinyDB:
        if self._static is None:
            storage = ReadOnlyMiddleware()
            self._static = tinydb.TinyDB(storage=storage, path=self._static_data_path, indent=2)
        return self._static

    def cars_data(self) -> tinydb.TinyDB:
        if self._cars is None:
            self._cars = tinydb.TinyDB(self._cars_data_path, indent=2)
        return self._cars

    def mem_db(self):
        if self._mem is None:
            self._mem = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
        return self._mem

    def close(self):
        if self._static:
            self._static.close()
        if self._cars:
            self._cars.close()
        if self._mem:
            self._mem.close()
