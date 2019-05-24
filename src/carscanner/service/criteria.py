from carscanner.allegro import CarscannerAllegro
from carscanner.dao.criteria import CriteriaDao, Criteria


class GetCategories:
    def __init__(self, allegro: CarscannerAllegro, dao: CriteriaDao):
        self._dao = dao
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

    def traverse_cats(self, result: list, cat=None, indent_level=0, stack=None):
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

        cats = self._allegro.get_categories(cat_id)

        for sub_cat in cats.categories:
            if self.keep_digging(sub_cat.name, stack + [cat_name]):
                self.traverse_cats(result, sub_cat, indent_level + 1, stack + [cat_name])

    def get_categories(self):
        result = []
        self.traverse_cats(result)
        return result

    def build_criteria(self):
        cats = self.get_categories()

        self._dao.purge()
        self._dao.insert_multiple([Criteria(cat['category_id']) for cat in cats])
