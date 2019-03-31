import logging

if __name__ == '__main__':
    from carscanner.main import main as main_func

    main_func()


def dump_file(data: dict, path: str) -> None:
    if path.endswith('.yml') or path.endswith('.yaml'):
        import yaml
        dump_f = yaml.safe_dump
    elif path.endswith('.json'):
        import json
        dump_f = json.dump
    elif path.endswith('.pickle'):
        import pickle
        dump_f = pickle.dump
    else:
        raise ValueError(path)

    with open(path, 'wt') as f:
        dump_f(data, f)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    for name in list(['carscanner', 'allegro_pl', '__main__']):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
