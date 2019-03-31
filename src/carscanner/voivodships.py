import logging
import os
import pickle

import tinydb

import carscanner
import carscanner.allegro

logger = logging.getLogger(__name__)


def _state_id(elem): return elem.stateId


def get_voivodships():
    client = carscanner.allegro.get_client()
    webapi_client = client.webapi_client()

    @client.retry
    def get_states_info(*args, **kwargs):
        return webapi_client.service.doGetStatesInfo(*args, **kwargs)

    states = get_states_info(1, client.oauth.client_id)

    # carscanner.dump_file(states, os.path.expanduser('~/.allegro/data/voivodeship.pickle'))

    _store(states)


def pickle_to_tinydb():
    with open(os.path.expanduser('~/.allegro/data/voivodeship.pickle'), 'br') as f:
        voivodeships = pickle.load(f)
        _store(voivodeships)


def _store(voivodeships) -> None:
    with tinydb.TinyDB(os.path.expanduser('~/.allegro/data/static.json'), indent=2) as db:
        tbl = db.table('voivodeship')
        db.purge_table('voivodeship')
        for v in sorted(voivodeships, key=_state_id):
            tbl.insert({'id': v.stateId, 'name': v.stateName})


if __name__ == '__main__':
    carscanner.configure_logging()
    get_voivodships()
    # pickle_to_tinydb()
