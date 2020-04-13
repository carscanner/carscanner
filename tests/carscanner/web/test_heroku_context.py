import os
import tempfile
from unittest import TestCase
from unittest.case import SkipTest

import pytel

from carscanner.context import Context, Config
from carscanner.service import GitBackupService


@SkipTest
class TestHerokuContext(TestCase):
    def test_context(self):
        os.environ['BACKUP_REMOTE'] = 'mock'
        os.environ['DATA_PATH'] = tempfile.gettempdir()
        from carscanner.web.heroku_context import HerokuContext

        with pytel.Pytel([Context(), HerokuContext(), {'config': Config()}]):
            pass

    def test_git_path(self):
        os.environ['BACKUP_REMOTE'] = 'mock'
        os.environ['DATA_PATH'] = tempfile.gettempdir()
        from carscanner.web.heroku_context import HerokuContext

        with pytel.Pytel([Context(), HerokuContext(), {'config': Config()}]) as ctx:
            b: GitBackupService = ctx.backup_svc
            self.assertNotEqual(b._data_path, b._vehicle_data_path)
