import pickle
import pprint
from os.path import expanduser as home
from unittest import TestCase

import allegro_api
import tinydb

from carscanner.car_offer import CarOffersBuilder, CarOfferBuilder
from carscanner.dao import VoivodeshipDao, CarMakeModelDao


class TestCarOffersBuilder(TestCase):
    def setUp(self) -> None:
        self.db = tinydb.TinyDB(home('~/.allegro/data/static.json'))

    def tearDown(self) -> None:
        self.db.close()

    def test_to_car_offers(self):
        offers_builder = CarOffersBuilder(VoivodeshipDao(self.db), CarMakeModelDao(self.db))

        with open(home('~/.allegro/data/listings.pickle'), 'br') as f:
            list: allegro_api.models.ListingResponse = pickle.load(f)
        car_offer_builders_dict = offers_builder.to_car_offers(list.items.promoted + list.items.regular)

        with open(home('~/.allegro/data/listing_7943513051.pickle'), 'br') as f:
            listings_details = pickle.load(f)
            for listing_details in listings_details.arrayItemListInfo.item:
                if listing_details.itemInfo.itId in car_offer_builders_dict:
                    builder: CarOfferBuilder = car_offer_builders_dict[listing_details.itemInfo.itId]
                    builder.update_from_item_info_struct(listing_details)

                    pprint.pprint(builder.c.to_dict())
