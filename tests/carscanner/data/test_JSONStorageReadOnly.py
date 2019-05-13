import os
from unittest import TestCase
import tempfile
from tinydb import TinyDB
from tinydb.database import Table
from carscanner.data.readonly import ReadOnlyMiddleware
from carscanner.utils import configure_logging


class TestJSONStorageReadOnly(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configure_logging()

    def test_readonly(self):
        fd, path = tempfile.mkstemp('.json')
        db = TinyDB(path)
        data: Table = db.table('data')
        data.insert({'a': 'b'})
        db.close()

        ro = TinyDB(path, storage=ReadOnlyMiddleware())
        tbl: Table = ro.table('data')
        tbl.insert({'c': 'd'})
        ro.close()

        print(path)
        os.close(fd)
