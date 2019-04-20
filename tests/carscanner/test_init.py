from unittest import TestCase

import toml

import carscanner


class TestInit(TestCase):
    def get_project_version(self):
        return toml.load('pyproject.toml')['tool']['poetry']['version']

    def test_version_matches(self):
        self.assertEqual(self.get_project_version(), carscanner.__version__)
