from unittest import TestCase

from carscanner.allegro.auth import TravisTokenStore


class TestTravisTokenStore(TestCase):
    def test_save(self):
        ts = TravisTokenStore()

        self.assertRaises(NotImplementedError, ts.save)

    def test_init(self):
        import os
        os.environ[TravisTokenStore.KEY_REFRESH_TOKEN] = 'test data'
        ts = TravisTokenStore()
        self.assertEqual('test data', ts.refresh_token)
        self.assertIsNone(ts.access_token)
