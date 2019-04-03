import json
import typing
from os.path import expanduser as xu

from tinydb import TinyDB
from unidecode import unidecode

from carscanner.allegro.dao.car_make_model import CarMakeModelDao


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


def load_car_list(path: str):
    with open(path, 'rt') as f:
        data = json.load(f)
    with TinyDB(xu('~/.allegro/data/static.json'), indent=2) as db:
        dao = CarMakeModelDao(db)
        dao.purge()
        for item in data:
            make = unidecode(item['brand'].lower())
            models = [unidecode(model).lower() for model in item['models']]
            dao.insert({'make': make, 'models': models})
