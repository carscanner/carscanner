import os
from unittest import TestCase

from carscanner.allegro.auth import EnvironClientCodeStore


class TestEnvironClientCodeStore(TestCase):
    def test_init(self):
        os.environ[EnvironClientCodeStore.KEY_CLIENT_ID] = 'a'
        os.environ[EnvironClientCodeStore.KEY_CLIENT_SECRET] = 'b'
        cs = EnvironClientCodeStore()
        self.assertEqual('a', cs.client_id)
        self.assertEqual('b', cs.client_secret)
