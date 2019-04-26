import datetime
from unittest import TestCase

from carscanner.utils import unix_to_datetime, datetime_to_unix

EPOCH_START = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, datetime.timezone.utc)


class test_utils(TestCase):
    def test_unix_to_datetime(self):
        self.assertEqual(EPOCH_START, unix_to_datetime(0))

    def test_datetime_tu_unix(self):
        self.assertEqual(0, datetime_to_unix(EPOCH_START))
