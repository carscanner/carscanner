import os
import tempfile
from unittest import TestCase

import pytel

from carscanner.context import Context, Config


class TestHerokuContext(TestCase):
    def test_context(self):
        os.environ['BACKUP_REMOTE'] = 'mock'
        os.environ['DATA_PATH'] = tempfile.gettempdir()
        from carscanner.web.heroku_context import HerokuContext

        ctx = pytel.Pytel([Context(), HerokuContext(), {'config': Config()}])
