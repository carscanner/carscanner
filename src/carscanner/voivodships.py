import logging

logger = logging.getLogger(__name__)
from carscanner.allegro import CarscannerAllegro as Allegro
from carscanner.dao import VoivodeshipDao


def _state_id(elem): return elem.stateId


class VoivodeshipService:
    def __init__(self, allegro: Allegro, dao: VoivodeshipDao):
        self.allegro = allegro
        self.dao = dao

    def load_voivodeships(self):
        states = self.allegro.get_states_info(1)

        data = [{'id': v.stateId, 'name': v.stateName} for v in states]
        self.dao.insert_multiple(data)
