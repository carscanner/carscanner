import carscanner
import carscanner.allegro
import logging

logger = logging.getLogger(__name__)


def get_voivodships():
    client = carscanner.allegro.get_client()
    webapi_client = client.webapi_client()

    @client.retry
    def get_states_info(*args, **kwargs):
        return webapi_client.service.doGetStatesInfo(*args, **kwargs)

    states = get_states_info(1, client.oauth.client_id)
    states_arr = []

    def state_id(elem): return elem.stateId

    for v in sorted(states, key=state_id):
        logger.debug(v.stateId)
        states_arr.append(v.stateName)

    with open('states.yml', 'wt') as f:
        import yaml
        yaml.safe_dump({'states': states_arr}, f)


if __name__ == '__main__':
    carscanner.configure_logging()
    get_voivodships()
