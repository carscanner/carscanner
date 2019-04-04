import pickle
import pprint
from os.path import expanduser as home
from unittest import TestCase

import tinydb
import zeep

from carscanner.allegro.car_offer import CarOffersBuilder, CarOfferBuilder
from carscanner.dao import VoivodeshipDao, CarMakeModelDao


class TestCarOffersBuilder(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        zeep.Client('https://webapi.allegro.pl/service.php?wsdl')

    def test_to_car_offers(self):
        db = tinydb.TinyDB(home('~/.allegro/data/static.json'))

        offers_builder = CarOffersBuilder(VoivodeshipDao(db), CarMakeModelDao(db))

        with open(home('~/.allegro/data/listings.pickle'), 'br') as f:
            list = pickle.load(f)
        car_offers = offers_builder.to_car_offers(list.items)
        car_offer_builders_dict = {b.c.id: b for b in car_offers}

        with open(home('~/.allegro/data/listing_7943513051.pickle'), 'br') as f:
            listings_details = pickle.load(f)
            for listing_details in listings_details.arrayItemListInfo.item:
                builder: CarOfferBuilder = car_offer_builders_dict[listing_details.itemInfo.itId]
                builder.update_from_item_info_struct(listing_details)

                pprint.pprint(builder.c.to_dict())
