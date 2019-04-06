from unittest import TestCase

from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from carscanner.dao import FilterDao


class TestFilterDao(TestCase):
    def setUp(self) -> None:
        self.db = TinyDB(storage=MemoryStorage)

    def tearDown(self) -> None:
        self.db.close()
        del self.db

    def test_names_to_keys_dict(self):
        dao = FilterDao(self.db)
        param_desc = {"category_id": "1",
                      "id": "startingTime",
                      "type": "SINGLE",
                      "name": "wystawione w ciągu",
                      "values": [
                          {
                              "value": "PT1H",
                              "name": "1 godziny",
                              "selected": False
                          },
                          {
                              "value": "PT2H",
                              "name": "2 godzin",
                              "selected": False
                          },

                      ]
                      }

        dao.insert(param_desc)
        result = dao.names_to_keys('1', 'wystawione w ciągu', '2 godzin')
        self.assertEqual(('startingTime', 'PT2H'), result)

    def test_names_to_keys_dict_missing_value(self):
        dao = FilterDao(self.db)
        param_desc = {"category_id": "1",
                      "id": "startingTime",
                      "type": "SINGLE",
                      "name": "wystawione w ciągu",
                      "values": [
                          {
                              "value": "PT1H",
                              "name": "1 godziny",
                              "selected": False
                          },
                          {
                              "value": "PT2H",
                              "name": "2 godzin",
                              "selected": False
                          },

                      ]
                      }
        dao.insert(param_desc)

        def get_name_no_value():
            dao.names_to_keys('1', 'wystawione w ciągu')

        self.assertRaises(ValueError, get_name_no_value)

    def test_names_to_keys_numeric(self):
        dao = FilterDao(self.db)
        param_desc = {
                         "category_id": '1',
                         "id": "price",
                         "type": "NUMERIC",
                         "name": "cena",
                         "values": [
                             {
                                 "idSuffix": ".from",
                                 "name": "od",
                                 "selected": False
                             },
                             {
                                 "idSuffix": ".to",
                                 "name": "do",
                                 "selected": False
                             }
                         ],
                         "minValue": 0,
                         "maxValue": 1000000000,
                         "unit": "zł"
                     }

        dao.insert(param_desc)

        def names_to_keys():
            result = dao.names_to_keys('1', 'cena')

        self.assertRaises(NotImplementedError, names_to_keys)
