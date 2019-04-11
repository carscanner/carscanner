from unittest import TestCase

import carscanner.allegro
from carscanner.allegro import YamlClientCodeStore, InsecureTokenStore


class TestAllegroServices(TestCase):

    def test_client_has_get_categories(self):
        service = carscanner.allegro.get_client(YamlClientCodeStore(), InsecureTokenStore())
        self.assertTrue(hasattr(service, 'get_categories'))
