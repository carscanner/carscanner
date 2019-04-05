import allegro_pl
from tinydb import TinyDB

import carscanner.allegro
from carscanner.dao.criteria import CriteriaDao, Criteria


class GetCategories:
    def __init__(self, allegro: allegro_pl.Allegro):
        self._allegro = allegro

    def keep_digging(self, name: str, stack: list):
        parent = stack[-1]
        if name == 'Motoryzacja' and parent != 'Ogłoszenia i usługi':
            return False
        else:
            return name in ['Allegro', 'Ogłoszenia i usługi', 'Motoryzacja', 'Samochody', 'Dostawcze (do 3.5 t)',
                            'Osobowe']

    def select_as_criteria(self, name: str, stack: list):
        return name in ['Dostawcze (do 3.5 t)', 'Osobowe']

    def get_cats(self, parent_id=None):
        """Pass parent_if argument only if it isn't None as the rest client doesn't accept None"""
        if parent_id is not None:
            return self._allegro.get_categories(parent_id=parent_id)
        else:
            return self._allegro.get_categories()

    def traverse_cats(self, result: list, cat=None, indent_level=0, stack=None):
        # indent = ' ' * (2 * indent_level)

        if stack is None:
            stack = []

        if cat is None:
            cat_name = 'Allegro'
            cat_id = None
        elif isinstance(cat, str):
            cat_name = 'Allegro'
            cat_id = cat
        else:
            cat_name = cat.name
            cat_id = cat.id

        if self.select_as_criteria(cat_name, stack):
            this = {'category_id': cat_id, 'cat_name': cat_name}
            result.append(this)

        cats = self.get_cats(cat_id)

        for sub_cat in cats.categories:
            if self.keep_digging(sub_cat.name, stack + [cat_name]):
                self.traverse_cats(result, sub_cat, indent_level + 1, stack + [cat_name])


def get_categories():
    allegro = carscanner.allegro.get_client()

    result = []

    GetCategories(allegro).traverse_cats(result)

    return result


def dump_categories():
    result = get_categories()
    from os.path import expanduser as xu
    with TinyDB(xu('~/.allegro/data/static.json'), indent=2) as db:
        dao = CriteriaDao(db)
        dao.purge()
        dao.insert_multiple([Criteria(cat['category_id']) for cat in result])


def print_categories():
    result = get_categories()
    import pprint
    pprint.pprint(result)


def criteria_build_cmd(**_):
    dump_categories()


if __name__ == '__main__':
    dump_categories()
    # print_categories()
