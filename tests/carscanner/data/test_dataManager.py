import os
import pathlib
from unittest import TestCase

from carscanner.data.data import DataManager


class TestDataManager(TestCase):
    def test_static_data(self):
        dm = DataManager('root_dir')

        expected_static_path = pathlib.Path('root_dir/static.json')
        self.assertEqual(expected_static_path, dm._static_data_path)

    def test_data(self):
        dm = DataManager('root_dir')

        expected_static_path = pathlib.Path('root_dir/cars.json')
        self.assertEqual(expected_static_path, dm._cars_data_path)
