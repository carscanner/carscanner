from carscanner.allegro import CarscannerAllegro
from carscanner.dao import VoivodeshipDao


class VoivodeshipService:
    def __init__(self, carscanner_allegro: CarscannerAllegro, voivodeship_dao: VoivodeshipDao):
        self._allegro = carscanner_allegro
        self._dao = voivodeship_dao

    def load_voivodeships(self):
        states = self._allegro.get_states_info()

        data = [{'id': v.stateId, 'name': v.stateName} for v in states]
        self._dao.insert_multiple(data)
