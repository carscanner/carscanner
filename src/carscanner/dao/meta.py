import dataclasses
import datetime
import logging
import platform
import typing

import pymongo

K_TS = 'timestamp'
META_V2 = 'meta'
META_VER: int = 5
"""Metadata file version expected by the software"""

log = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Metadata:
    host: str
    timestamp: datetime.datetime
    version: int

    @staticmethod
    def from_dict(d: dict) -> 'Metadata':
        return Metadata(host=d['host'], timestamp=d['timestamp'], version=d['version'])

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class MetadataDao:
    def __init__(self, meta_col: pymongo.collection.Collection):
        self._col = meta_col
        self._meta: typing.Optional[Metadata] = None

        raw_meta = self._col.find_one({})
        self._meta = Metadata.from_dict(raw_meta) if raw_meta else MetadataDao._init_metadata()
        assert self._meta.version == META_VER

    def update(self, ts: datetime.datetime):
        if ts is None:
            raise AttributeError('ts is None')
        self._meta = Metadata(host=platform.node(), timestamp=ts, version=META_VER)
        self._col.update_one({}, {'$set': self._meta.to_dict()}, upsert=True)

    def report(self):
        if self._meta:
            log.info('Last run at %s on %s', self._meta.timestamp.isoformat(), self._meta.host)
        else:
            log.info('First run')

    def get_timestamp(self) -> datetime.datetime:
        return self._meta.timestamp

    @staticmethod
    def _init_metadata() -> Metadata:
        return Metadata(platform.node(), None, META_VER)
