import os

import allegro_api
import allegro_pl

from .auth import AuthorizationCodeAuth, EnvironClientCodeStore, InsecureTokenStore, YamlClientCodeStore


def get_root():
    root_var = '~/.allegro'
    root = os.path.expanduser(root_var)
    auth_dir = os.path.join(root, 'auth')
    if not os.path.exists(root):
        os.mkdir(root, 0o700)
        os.mkdir(auth_dir)
    return root, auth_dir


root, auth_dir = get_root()
codes_path = os.path.join(auth_dir, 'allegro.yaml')
token_path = os.path.join(auth_dir, 'insecure-tokens.yaml')


class CarscannerAllegro(allegro_pl.Allegro):
    def __init__(self, oauth):
        super().__init__(oauth)

        rest_client = self.rest_api_client()
        webapi_client = self.webapi_client()
        cat_service = allegro_api.api.CategoriesAndParametersApi(rest_client)
        public_offer_service = allegro_api.api.PublicOfferInformationApi(rest_client)
        cat_api = allegro_api.api.CategoriesAndParametersApi(rest_client)

        @self.retry
        def get_categories(**kwargs):
            return cat_service.get_categories_using_get(**kwargs)

        self.get_categories = get_categories

        @self.retry
        def get_listing(search_params):
            return public_offer_service.get_listing(search_params)

        self.get_listing = get_listing
        self.get_listing.limit_min = 1
        self.get_listing.limit_max = 100

        @self.retry
        def get_items_info(**kwargs):
            """This """
            if kwargs.get('sessionHandle') is None:
                kwargs['sessionHandle'] = self.webapi_session_handle
            if 'itemsIdArray' in kwargs:
                items_id_array = webapi_client.get_type('ns0:ArrayOfLong')(kwargs['itemsIdArray'])
                kwargs['itemsIdArray'] = items_id_array
            return webapi_client.service.doGetItemsInfo(**kwargs)

        self.get_items_info = get_items_info
        self.get_items_info.items_limit = 10

        @self.retry
        def get_category_parameters(category_id: str, **kwargs) -> allegro_api.models.CategoryParameterList:
            return cat_api.get_flat_parameters_using_get2(category_id, **kwargs)

        self.get_category_parameters = get_category_parameters

    def get_categories(self, **kwags) -> allegro_api.models.CategoriesDto:
        pass

    def get_listing(self, search_params: dict) -> allegro_api.models.ListingResponse:
        pass

    def get_items_info(self, **kwargs):
        pass

    def get_category_parameters(self, category_id: str, **kwargs) -> allegro_api.models.CategoryParameterList:
        pass


def get_client(code_store, token_store: allegro_pl.TokenStore) -> CarscannerAllegro:
    if code_store is None:
        code_store = YamlClientCodeStore()

    if token_store is None:
        token_store = InsecureTokenStore(token_path)

    auth = AuthorizationCodeAuth(code_store, token_store)
    return CarscannerAllegro(auth)
