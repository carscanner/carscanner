import logging

import allegro_api.api
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
    def get_listing(**kwargs):
        return offer_api.get_listing(**kwargs)

    # data = get_listing(category_id='46088', sort='-startTime', fallback=False, starting_time='P2D')
    data = get_listing(category_id='257753', fallback=False,
                       include=['-all', 'items', 'searchMeta'],
                       parameter_215882=272070,  # oferta dotyczy sprzedaży
                       parameter_11323=2,  # stan = używane
                       starting_time='P2D',  # ostatnie 2 dni
                       limit=10,
                       )

    items = data.items

    logger.info(str(len(items.promoted)) + '+' + str(len(items.regular)))

    # carscanner.dump_file(data.to_dict(), 'cat_257753.json')
    import pickle
    with open('listings.pickle', 'bw') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    webapi_client = client.webapi_client()

    @client.retry
    def get_item_info_ext(*args, **kwargs):
        return webapi_client.service.doShowItemInfoExt(*args, **kwargs)

    offer_id = (items.promoted + items.regular)[0].id
    offer_ext = get_item_info_ext(client.webapi_session_handle, offer_id, getImageUrl=1, getAttribs=1)

    logger.debug(type(offer_ext))

    # carscanner.dump_file(webapi_dump(offer_ext), 'offer_' + str(offer_id) + '.json')
    with open('listing_' + offer_id + '.pickle', 'wb') as f:
        pickle.dump(offer_ext, f, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    carscanner.configure_logging()

    get_offers()
