import logging
import typing


def dump_file(data: typing.Any, path: str) -> None:
    if path.endswith('.yml') or path.endswith('.yaml'):
        import yaml
        dump_f = yaml.safe_dump
        mode = 'wt'
    elif path.endswith('.json'):
        import json
        dump_f = json.dump
        mode = 'wt'
    elif path.endswith('.pickle'):
        import pickle
        dump_f = pickle.dump
        mode = 'wb'
    else:
        raise ValueError(path)

    with open(path, mode) as f:
        dump_f(data, f)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    for name in list(['carscanner', 'allegro_pl', '__main__']):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
