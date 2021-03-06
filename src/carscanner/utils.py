import datetime
import functools
import logging
import pathlib
import time
import typing


def datetime_to_unix(dt: datetime.datetime) -> int:
    return int(dt.timestamp())


def unix_to_datetime(timestamp: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    for name, level in {'carscanner': logging.DEBUG,
                        'allegro_pl': logging.DEBUG,
                        '__main__': logging.DEBUG,
                        'tenacity': logging.WARN
                        }.items():
        log = logging.getLogger(name)
        log.setLevel(level)


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


def join_str(separator: str, *args) -> str:
    return separator.join(arg for arg in args if arg is not None)


def _ignore_file_handler(_: pathlib.Path) -> None:
    pass


def walk_path(path: pathlib.Path, file_handler: typing.Callable[[pathlib.Path], None] = _ignore_file_handler) -> None:
    for i in sorted(path.iterdir()):
        if i.is_dir():
            walk_path(i, file_handler)
        else:
            file_handler(i)
