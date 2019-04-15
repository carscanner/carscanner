import json
import typing

from unidecode import unidecode

from carscanner.dao import CarMakeModelDao


def derive_model(car_make_model: CarMakeModelDao, make: str, name: str, description: str) -> typing.Optional[str]:
    assert make

    if name is None and description is None:
        raise ValueError('name or description required')

    models = car_make_model.get_models_by_make(make)

    name = name.lower() if name is not None else ''
    description = description.lower() if description is not None else ''

    matches = []
    for model in models:
        if model in name or model in description:
            matches.append(model.capitalize())

    return max(matches, key=len, default=None)


class CarMakeModelService:
    def __init__(self, dao: CarMakeModelDao):
        self._dao = dao

    def load_car_list(self, path: str):
        with open(path, 'rt') as f:
            data = json.load(f)
            self._dao.purge()
            for item in data:
                make = unidecode(item['brand'].lower())
                models = [unidecode(model).lower() for model in item['models']]
                self._dao.insert({'make': make, 'models': models})

    def show_car_list(self):
        for doc in self._dao.all():
            print(doc['make'])
            for model in doc['models']:
                print(' ', model)
