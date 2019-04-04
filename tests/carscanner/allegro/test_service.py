from unittest import TestCase
import carscanner.allegro


class TestAllegroServices(TestCase):

    def test_client_has_get_categories(self):
        service = carscanner.allegro.get_client()
        self.assertTrue(hasattr(service, 'get_categories'))
