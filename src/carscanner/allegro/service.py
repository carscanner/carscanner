import allegro_api.api


def init_service_methods(allegro) -> None:
    allegro_t = type(allegro)

    cat_service = allegro_api.api.CategoriesAndParametersApi(allegro.rest_api_client())

    @allegro.retry
    def get_categories(self, **kwargs):
        return cat_service.get_categories_using_get(**kwargs)

    allegro_t.get_categories = get_categories


