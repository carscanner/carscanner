import logging
import typing

import allegro_api

from carscanner.allegro import CarscannerAllegro
from carscanner.dao import CriteriaDao, FilterDao, Criteria

log = logging.getLogger(__name__)
crit = Criteria('4029', 'Osobowe')


class FilterService:
    def __init__(self, carscanner_allegro: CarscannerAllegro, filter_dao: FilterDao, criteria_dao: CriteriaDao):
        self._allegro = carscanner_allegro
        self._filter_dao = filter_dao
        self._crit_dao = criteria_dao

    def load_filters(self):
        log.debug("Get filters for %s", crit.category_name)
        self._filter_dao.purge()
        filters = self._allegro.get_filters(crit.category_id)
        for filt in filters:
            filt = FilterService._filter_to_dict(crit.category_id, filt)
            self._filter_dao.insert(filt)

    @staticmethod
    def _filter_to_dict(cat_id, param: allegro_api.models.ListingResponseFilters) -> dict:
        param_dict = param.to_dict()
        return param_dict

    def transform_filters(self, category_id, filters: typing.Dict[str, str]) -> typing.Dict[str, str]:
        result = {}
        for k, v in filters.items():
            nk, nv = self._filter_dao.names_to_keys(category_id, k, v)
            result[nk] = nv

        return result
