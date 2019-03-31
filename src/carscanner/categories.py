import allegro_api.api
import allegro_pl
import yaml

import carscanner.allegro


class GetCategories:
    def __init__(self, allegro: allegro_pl.Allegro, ):
        self._allegro = allegro
        api_client = allegro.rest_api_client()
        self._cat_api = allegro_api.api.CategoriesAndParametersApi(api_client)

    def i_like_this_category(self, name: str, stack: list) -> bool:
        parent = stack[-1]
        if name == 'Motoryzacja' and parent != 'Ogłoszenia i usługi':
            return False
        elif name == 'Pozostałe' and parent == 'Osobowe':
            return False
        else:
            return name in ['Allegro', 'Ogłoszenia i usługi', 'Motoryzacja', 'Samochody',
                            'Dostawcze (do 3.5 t)', 'Osobowe'] or 'Osobowe' in stack

    def traverse_cats(self, result: dict, cat=None, indent_level=0, stack=None):
        indent = ' ' * (2 * indent_level)

        if stack is None:
            stack = []

        @self._allegro.retry
        def get_cats(**kwargs):
            return self._cat_api.get_categories_using_get(**kwargs)

        if cat is None:
            cat_name = 'Allegro'
            cat_id = None
        elif isinstance(cat, str):
            cat_name = 'Allegro'
            cat_id = cat
        else:
            cat_name = cat.name
            cat_id = cat.id

        this = {'id': cat_id}
        children = {}
        cats = get_cats(parent_id=cat_id) if cat_id else get_cats()  # can't pass None to get root categories
        for sub_cat in cats.categories:
            print(indent, sub_cat)
            if self.i_like_this_category(sub_cat.name, stack + [cat_name]):
                this_child = {}
                self.traverse_cats(this_child, sub_cat, indent_level + 1, stack + [cat_name])
                children.update(this_child)
        if len(children):
            this['children'] = children
        result[cat_name] = this


def get_categories():
    allegro = carscanner.allegro.get_client()

    result = {}

    GetCategories(allegro).traverse_cats(result)

    # pprint.pprint(result)
    with open('cat_tree.yml', 'tw') as f:
        yaml.safe_dump(result, f)
    # print(api_client)


if __name__ == '__main__':
    get_categories()
