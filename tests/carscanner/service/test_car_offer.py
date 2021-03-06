import datetime
import logging
from pprint import pprint
from unittest import TestCase

import pytel
import pytest
from allegro_api import ListingOffer

from carscanner.cli.cmd import CmdContext
from carscanner.context import ENV_LOCAL, Context, Config
from carscanner.dao import CarOffer
from carscanner.service.car_offer import _update_from_item_info_attributes


@pytest.mark.timeout(90, method='thread')
@pytest.mark.web
class TestWebCarOffer(TestCase):
    def test__update_from_item_info_attributes(self):
        # zeep doesn't seem test friendly, had problem with creating value objects manually

        import argparse
        import carscanner.utils

        carscanner.utils.configure_logging()
        log = logging.getLogger(__name__)

        ns = argparse.Namespace(
            environment=ENV_LOCAL,
            data='~/projects/carscanner-data/',
        )

        config = Config()
        config.allow_fetch = True

        with pytel.Pytel([
            Context(),
            CmdContext(ns),
            {
                'config': config,
            }
        ]) as ctx:
            ctx.filter_svc.load_filters()

            crit = [crit for crit in ctx.criteria_dao.all() if crit.category_name.lower() == 'bmw'][0]

            allegro = ctx.carscanner_allegro
            offers_svc = ctx.offers_svc
            params = offers_svc._search_params(crit, 0)
            pprint(params)
            params['limit'] = allegro.get_listing.limit_min
            params['category_id'] = crit.category_id

            listing_offer: ListingOffer = allegro.get_listing(**params).items.promoted[0]

            ctx.allegro.soap_service().login_with_access_token()

            log.info("get_items_info(%s)", listing_offer.id)
            items_info_result = offers_svc._do_get_items_info([listing_offer.id])
            car_item_info = items_info_result[0]

            ts = datetime.datetime.utcnow()
            car_offer = CarOffer(ts)
            attribs = {a.attribName: a.attribValues.item for a in car_item_info.itemAttribs.item}
            _update_from_item_info_attributes(car_offer, attribs)

            pprint(car_offer)
