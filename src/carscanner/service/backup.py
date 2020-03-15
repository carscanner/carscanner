import abc

from carscanner.dao import CarOffer
from carscanner.dao.car_offer import _K_PRICE, _K_FIRST_SPOTTED, _K_LAST_SPOTTED
from carscanner.utils import datetime_to_unix


class BackupService(metaclass=abc.ABCMeta):
    def backup(self):
        pass

    @staticmethod
    def _convert(obj: CarOffer) -> dict:
        result = obj.__dict__.copy()
        result[_K_PRICE] = str(obj.price)
        result[_K_FIRST_SPOTTED] = datetime_to_unix(obj.first_spotted)
        if obj.last_spotted:
            result[_K_LAST_SPOTTED] = datetime_to_unix(obj.last_spotted)

        return result

