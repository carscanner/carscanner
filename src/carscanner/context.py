import abc
import concurrent.futures as futures
import datetime
import pathlib
import typing

import allegro_pl
import pymongo
import pymongo.database
import tinydb

import carscanner
import carscanner.allegro
import carscanner.dao
import carscanner.data
import carscanner.service
from carscanner.utils import memoized, unix_to_datetime


class Context(metaclass=abc.ABCMeta):
    def __init__(self):
        self._modify_static = False
        self._closers: typing.List[typing.Callable] = []

    @memoized
    def allegro(self):
        return carscanner.allegro.CarscannerAllegro(self.allegro_client())

    @abc.abstractmethod
    def allegro_auth(self):
        pass

    @memoized
    def allegro_client(self):
        return allegro_pl.Allegro(self.allegro_auth())

    @memoized
    def car_makemodel_dao(self):
        return carscanner.dao.CarMakeModelDao(self.static_data())

    @memoized
    def car_makemodel_svc(self):
        return carscanner.service.CarMakeModelService(self.car_makemodel_dao())

    @memoized
    def car_offers_builder(self):
        return carscanner.service.CarOffersBuilder(
            self.voivodeship_dao(),
            self.car_makemodel_dao(),
            self.datetime_now(),
        )

    @memoized
    def car_offer_dao(self):
        return carscanner.dao.CarOfferDao(self.vehicle_collection_v4())

    @memoized
    def categories_svc(self):
        return carscanner.service.GetCategories(self.allegro(), self.criteria_dao())

    def close(self):
        for close in reversed(self._closers):
            close()

    @memoized
    def criteria_dao(self):
        return carscanner.dao.CriteriaDao(self.static_data())

    @memoized
    def datetime_now(self) -> datetime.datetime:
        return unix_to_datetime(self.timestamp())

    @memoized
    def executor(self):
        executor = futures.ThreadPoolExecutor()

        self._closers.append(lambda: executor.shutdown(True))
        return executor

    @property
    @abc.abstractmethod
    def data_path(self) -> pathlib.Path:
        pass

    @memoized
    def file_backup_service(self):
        return carscanner.service.FileBackupService(self.car_offer_dao(), self.vehicle_data_path_v3())

    @memoized
    def filter_dao(self):
        return carscanner.dao.FilterDao(self.mem_db())

    @memoized
    def filter_svc(self):
        return carscanner.service.FilterService(
            self.allegro(),
            self.filter_dao(),
            self.criteria_dao())

    @memoized
    def mem_db(self):
        db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
        self._closers.append(db.close)
        return db

    @memoized
    def meta_col(self):
        from carscanner.dao.meta import META_V2
        db = self.mongodb_carscanner_db()
        return db.get_collection(META_V2, codec_options=db.codec_options)

    @memoized
    def metadata_dao(self):
        return carscanner.dao.MetadataDao(self.meta_col())

    @memoized
    def migration_service(self):
        return carscanner.service.migration.MigrationService(
            self.mongodb_carscanner_db(),
        )

    @property
    def modify_static(self):
        return self._modify_static

    @modify_static.setter
    def modify_static(self, value: bool) -> None:
        self._modify_static = value

    @memoized
    def mongodb_carscanner_db(self) -> pymongo.database.Database:
        conn = self.mongodb_connection()
        return conn.get_database(codec_options=conn.codec_options)

    @memoized
    def mongodb_connection(self) -> pymongo.MongoClient:
        import os
        return pymongo.MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost/carscanner'), retryWrites=False)

    @memoized
    def offer_export_svc(self):
        return carscanner.service.ExportService(self.car_offer_dao(), self.metadata_dao())

    @memoized
    def offers_svc(self):
        return carscanner.service.OfferService(
            self.allegro(),
            self.criteria_dao(),
            self.car_offers_builder(),
            self.car_offer_dao(),
            self.filter_svc(),
            self.datetime_now(),
        )

    @memoized
    def static_data(self) -> tinydb.TinyDB:
        import carscanner.dao.resources
        storage = carscanner.data.ResourceStorage
        storage = storage if self.modify_static else carscanner.data.ReadOnlyMiddleware(storage)
        db = tinydb.TinyDB(storage=storage, package=carscanner.dao.resources, resource='static.json', indent=2)
        self._closers.append(db.close)
        return db

    @memoized
    def timestamp(self):
        return carscanner.utils.now()

    @memoized
    def token_collection(self):
        db = self.mongodb_carscanner_db()
        return db.get_collection('token', codec_options=db.codec_options)

    @memoized
    def vehicle_collection_v4(self):
        from carscanner.dao.car_offer import VEHICLE_V3
        db = self.mongodb_carscanner_db()
        return db.get_collection(VEHICLE_V3, codec_options=db.codec_options)

    @memoized
    def vehicle_data_path_v3(self) -> pathlib.Path:
        from carscanner.dao.car_offer import VEHICLE_V3

        data_path = self.data_path / VEHICLE_V3
        return data_path

    @memoized
    def vehicle_updater(self):
        return carscanner.service.VehicleUpdaterService(
            self.offers_svc(),
            self.metadata_dao(),
            self.filter_svc(),
            self.offer_export_svc(),
            self.datetime_now(),
            self.data_path,
            self.file_backup_service(),
            self.executor(),
        )

    @memoized
    def voivodeship_dao(self):
        return carscanner.dao.VoivodeshipDao(self.static_data())

    @memoized
    def voivodeship_svc(self):
        return carscanner.service.VoivodeshipService(self.allegro(), self.voivodeship_dao())
