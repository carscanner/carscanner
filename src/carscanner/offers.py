import logging
import pickle
from os.path import expanduser as xu

import allegro_api.api
import allegro_pl
import zeep

import carscanner.allegro

logger = logging.getLogger(__name__)


def webapi_dump(obj):
    if isinstance(obj, list):
        return [webapi_dump(x) for x in obj]
    elif isinstance(obj, (dict, zeep.xsd.CompoundValue)):
        return {k: webapi_dump(v) for k, v in obj}
    else:
        return obj


def get_offers():
    client = carscanner.allegro.get_client()
    rest_client = client.rest_api_client()
    offer_api = allegro_api.api.PublicOfferInformationApi(rest_client)

    @client.retry
    def get_listing(search_params) -> allegro_api.models.ListingResponse:
        return offer_api.get_listing(search_params)

    data = get_listing({'category.id': '257753', 'fallback': False,
                        # 'include': ['-all', 'items', 'searchMeta'],
                        'parameter.215882': 272070,  # oferta dotyczy sprzedaży
                        'parameter.11323': 2,  # stan = używane
                        'starting.time': 'P2D',  # ostatnie 2 dni
                        'limit': 10}
                       )

    items = data.items

    logger.info(str(len(items.promoted)) + '+' + str(len(items.regular)))

    carscanner.dump_file(data, xu('~/.allegro/data/listings.pickle'))

    _get_item_info(client, items)


def get_items_info(client: allegro_pl.Allegro):
    with open(xu('~/.allegro/data/listings.pickle'), 'br') as f:
        data = pickle.load(f)
    _get_item_info(client, data.items)


def _get_item_info(client: allegro_pl.Allegro, items: allegro_api.models.ListingResponseOffers):
    webapi_client = client.webapi_client()

    @client.retry
    def get_item_info(*args, **kwargs):
        # return webapi_client.service.doShowItemInfoExt(*args, **kwargs)
        return webapi_client.service.doGetItemsInfo(*args, **kwargs)

    my_items = (items.promoted + items.regular)[0:10]
    offer_id = webapi_client.get_type('ns0:ArrayOfLong')([int(item.id) for item in my_items])
    offer_ext: zeep.xsd.CompoundValue = get_item_info(client.webapi_session_handle, offer_id, getDesc=1, getImageUrl=1,
                                                      getAttribs=1)

    path = xu('~/.allegro/data/listing_' + str(my_items[0].id) + '-' + str(my_items[9].id) + '.pickle')
    carscanner.dump_file(offer_ext, path)


if __name__ == '__main__':
    carscanner.configure_logging()

    get_offers()

    # client = carscanner.allegro.get_client()
    # get_items_info(client)
