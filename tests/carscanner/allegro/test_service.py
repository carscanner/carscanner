import os
from unittest import TestCase

import carscanner.allegro
from carscanner.allegro import EnvironClientCodeStore
from carscanner.allegro.auth import TravisTokenStore


class TestAllegroServices(TestCase):

    def test_client_has_get_categories(self):
        os.environ['ALLEGRO_CLIENT_ID'] = 'a'
        os.environ['ALLEGRO_CLIENT_SECRET'] = 'b'
        os.environ['ALLEGRO_REFRESH_TOKEN'] = 'c'
        service = carscanner.allegro.get_client(EnvironClientCodeStore(), TravisTokenStore())
        self.assertTrue(hasattr(service, 'get_categories'))
