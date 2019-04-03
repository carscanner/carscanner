import tinydb


class BaseDao:
    def __init__(self, db: tinydb.TinyDB):
        self._db = db
