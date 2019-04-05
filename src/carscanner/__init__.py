import logging

from .car_offer import CarOffer, CarOffersBuilder, CarOfferBuilder


def dump_file(data, path: str) -> None:
    if path.endswith('.yml') or path.endswith('.yaml'):
        import yaml
        dump_f = yaml.safe_dump
        mode = 'wt'
    elif path.endswith('.json'):
        import json
        dump_f = json.dump
        mode = 'wt'
    elif path.endswith('.pickle'):
        def dump_f(data, stream):
            import pickle
            pickle.dump(data, stream, protocol=pickle.HIGHEST_PROTOCOL)

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


def webapi_dump(obj):
    import zeep.xsd

    if isinstance(obj, list):
        return [webapi_dump(x) for x in obj]
    elif isinstance(obj, (dict, zeep.xsd.CompoundValue)):
        return {k: webapi_dump(v) for k, v in obj}
    else:
        return obj


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i + n]
