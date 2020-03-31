import datetime
from unittest import TestCase

from carscanner.utils import unix_to_datetime, datetime_to_unix, join_str, chunks

EPOCH_START = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, datetime.timezone.utc)

_SEP = ' SEP '


class UtilsTest(TestCase):
    def test_unix_to_datetime(self):
        self.assertEqual(EPOCH_START, unix_to_datetime(0))

    def test_datetime_tu_unix(self):
        self.assertEqual(0, datetime_to_unix(EPOCH_START))

    def test_join_str_empty(self):
        self.assertEqual('', join_str(_SEP))

    def test_join_str_single(self):
        self.assertEqual('str', join_str(_SEP, 'str'))

    def test_join_str_single_none(self):
        self.assertEqual('', join_str(_SEP, None))

    def test_join_str_two(self):
        self.assertEqual('1 SEP 2', join_str(_SEP, '1', '2'))

    def test_join_str_two_none(self):
        self.assertEqual('', join_str(_SEP, None, None))

    def test_join_str_two_with_none(self):
        self.assertEqual('1', join_str(_SEP, '1', None))

    def test_chunks(self):
        my_range = range(10)
        my_chunks = list(chunks(list(my_range), 5))
        self.assertEqual([[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]], my_chunks)

    def test_chunks_empty(self):
        self.assertEqual([], list(chunks([], 8)))
