import bisect
import datetime
import logging
import typing

import allegro_api
import isodate

from carscanner.allegro import CarscannerAllegro
from carscanner.dao import CriteriaDao, FilterDao, Criteria

log = logging.getLogger(__name__)
crit = Criteria('4029', 'Osobowe')


class FilterService:
    def __init__(self, allegro: CarscannerAllegro, filter_dao: FilterDao, crit_dao: CriteriaDao):
        self._allegro = allegro
        self._filter_dao = filter_dao
        self._crit_dao = crit_dao

    def load_filters(self):
        log.debug("Get filters for %s", crit.category_name)
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

    def find_min_timedelta_gt(self, cat_id: str, delta: datetime.timedelta) -> typing.Optional[datetime.timedelta]:
        doc = self._filter_dao.get_required(cat_id, 'wystawione w ciągu')
        durations = sorted([isodate.parse_duration(duration['value']) for duration in doc['values']])
        idx = bisect.bisect_left(durations, delta)
        if idx == len(durations):
            return None
        else:
            return durations[idx]
