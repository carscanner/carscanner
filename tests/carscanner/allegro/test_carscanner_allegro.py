from unittest import TestCase
from unittest.mock import Mock

from carscanner.allegro import CarscannerAllegro


class TestCarscannerAllegro(TestCase):
    def test_init(self):
        allegro = Mock()
        rest_service = Mock()
        soap_service = Mock()
        allegro.rest_service = Mock(return_value=rest_service)
        allegro.soap_service = Mock(return_value=soap_service)

        t = CarscannerAllegro(allegro)

        self.assertEqual(t.get_categories, rest_service.get_categories)
        self.assertEqual(t.get_category_parameters, rest_service.get_category_parameters)
        self.assertEqual(t.get_items_info, soap_service.get_items_info)
        self.assertEqual(t.get_listing, rest_service.get_listing)
        self.assertEqual(t.get_states_info, soap_service.get_states_info)

    def test_get_filters(self):
        allegro = Mock()
        rest_service = Mock()
        soap_service = Mock()
        allegro.rest_service = Mock(return_value=rest_service)
        allegro.soap_service = Mock(return_value=soap_service)

        t = CarscannerAllegro(allegro)

        t.get_filters('my_cat_id')

        rest_service.get_listing.assert_called_once_with(
            category_id='my_cat_id',
            limit=rest_service.get_listing.limit_min,
            include=['-all', 'filters'],
            _request_timeout=(30, 30),
        )
