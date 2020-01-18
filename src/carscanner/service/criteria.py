import typing

from carscanner.allegro import CarscannerAllegro
from carscanner.dao.criteria import CriteriaDao, Criteria

allowed_cat_stacks = [
    ['Allegro', 'Ogłoszenia i usługi', 'Motoryzacja', 'Samochody', 'Osobowe'],
]

skip = ['Pozostałe']


class GetCategories:
    def __init__(self, allegro: CarscannerAllegro, dao: CriteriaDao):
        self._dao = dao
        self._allegro = allegro

    @staticmethod
    def keep_digging(stack: list):
        for allowed_stack in allowed_cat_stacks:
            if len(stack) <= len(allowed_stack) and stack == allowed_stack[:len(stack)]:
                return True
        else:
            return False

    @staticmethod
    def select_as_criteria(name: str, stack: list):
        return stack in allowed_cat_stacks

    def traverse_cats(self, result: typing.List[Criteria], cat=None, stack=None):
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

        if cat_name in skip:
            return

        if self.select_as_criteria(cat_name, stack):
            this = Criteria(cat_id, cat_name)
            result.append(this)

        if self.keep_digging(stack + [cat_name]):
            cats = self._allegro.get_categories(cat_id)
            for sub_cat in cats.categories:
                self.traverse_cats(result, sub_cat, stack + [cat_name])

    def get_categories(self):
        result = []
        self.traverse_cats(result)
        return result

    def build_criteria(self):
        cats = self.get_categories()

        self._dao.purge()
        self._dao.insert_multiple(cats)
