import datetime
import functools
import logging
import time


def datetime_to_unix(dt: datetime.datetime) -> int:
    return int(dt.timestamp())


def unix_to_datetime(timestamp: int) -> datetime:
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    for name, level in {'carscanner': logging.DEBUG,
                        'allegro_pl': logging.DEBUG,
                        '__main__': logging.DEBUG,
                        'tenacity': logging.WARN
                        }.items():
        log = logging.getLogger(name)
        log.setLevel(level)
        log.addHandler(handler)


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i + n]


def memoized(obj):
    @functools.wraps(obj)
    def memoizer(self=None):
        if not hasattr(obj, 'cache'):
            obj.cache = obj(self)

        return obj.cache

    return memoizer


def now():
    return int(time.time())
