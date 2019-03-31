import pprint

import allegro_api.api

import carscanner.allegro


def main():
    client = carscanner.allegro.get_client()
    rest_client = client.rest_api_client()
    cat_api = allegro_api.api.CategoriesAndParametersApi(rest_client)

    @client.retry
    def get_params(category_id: str, **kwargs):
        return cat_api.get_flat_parameters_using_get2(category_id, **kwargs)

    result = get_params('255460')
    pprint.pprint(result)


if __name__ == '__main__':
    main()
