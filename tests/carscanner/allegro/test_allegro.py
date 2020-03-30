from unittest import TestCase
from unittest.mock import patch, Mock


class AllegroTest(TestCase):
    @patch('pathlib.Path')
    def test_get_root_exists(self, path_mock):
        import carscanner.allegro.allegro as allegro

        expanded = path_mock('~/.carscanner').expanduser()
        expanded.exists = Mock(return_value=True)

        allegro.get_root()

        expanded.exists.assert_called_once_with()
        expanded.mkdir.assert_not_called()

    @patch('pathlib.Path')
    def test_get_root_not_exists(self, path_mock):
        import carscanner.allegro.allegro as allegro

        expanded = path_mock('~/.carscanner').expanduser()
        expanded.exists = Mock(return_value=False)

        allegro.get_root()

        expanded.exists.assert_called_once_with()
        expanded.mkdir.assert_called_once()
