from unittest import TestCase

import allegro_api

from carscanner.service import FilterService


class TestFilterService(TestCase):
    def test__transform_param(self):
        param = allegro_api.models.ListingResponseFilters(id='startingTime', name='wystawione w ciągu')
        actual = FilterService._filter_to_dict('a category', param)
        expected = {
            'category_id': 'a category',
            "id": "startingTime",
            "name": "wystawione w ciągu",
            'max_value': None,
            'min_value': None,
            'type': None,
            'unit': None,
            'values': None
        }
        self.assertEqual(expected, actual)
