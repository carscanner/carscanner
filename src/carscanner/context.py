import argparse
import concurrent.futures as futures
import contextlib
import dataclasses
import datetime
import pathlib

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

ENV_TRAVIS = 'travis'
ENV_LOCAL = 'local'


@dataclasses.dataclass
class Config:
    allow_fetch = False
    modify_static = False


class Context:
    def allegro_auth(self,
                     config: Config,
                     client_code_store: allegro_pl.ClientCodeStore,
                     token_store: allegro_pl.oauth.TokenStore
                     ) -> allegro_pl.oauth.AllegroAuth:
        return carscanner.allegro.CarScannerCodeAuth(client_code_store, token_store, config.allow_fetch)

    def allegro(self, allegro_auth: allegro_pl.oauth.AllegroAuth) -> allegro_pl.Allegro:
        return allegro_pl.Allegro(allegro_auth)

    def car_make_model_dao(self, static_data: tinydb.TinyDB) -> carscanner.dao.CarMakeModelDao:
        return carscanner.dao.CarMakeModelDao(static_data)

    car_makemodel_svc = carscanner.service.CarMakeModelService

    car_offers_builder = carscanner.service.CarOffersBuilder

    def car_offer_dao(self, vehicle_collection_v4: pymongo.collection.Collection) -> carscanner.dao.CarOfferDao:
        return carscanner.dao.CarOfferDao(vehicle_collection_v4)

    carscanner_allegro = carscanner.allegro.CarscannerAllegro

    categories_svc = carscanner.service.GetCategories

    def client_code_store(self, ns: argparse.Namespace) -> allegro_pl.ClientCodeStore:
        if ns.environment == ENV_LOCAL:
            return carscanner.allegro.YamlClientCodeStore(carscanner.allegro.codes_path)
        elif ns.environment == ENV_TRAVIS:
            return carscanner.allegro.EnvironClientCodeStore()
        else:
            raise ValueError(ns.environment)

    def criteria_dao(self, static_data: tinydb.TinyDB) -> carscanner.dao.CriteriaDao:
        return carscanner.dao.CriteriaDao(static_data)

    def datetime_now(self, timestamp: int) -> datetime.datetime:
        return unix_to_datetime(timestamp)

    @contextlib.contextmanager
    def executor(self) -> futures.ThreadPoolExecutor:
        executor = futures.ThreadPoolExecutor()
        try:
            yield executor
        finally:
            executor.shutdown(True)

    def file_backup_service(self, car_offer_dao: carscanner.dao.CarOfferDao, vehicle_data_path_v3: pathlib.Path) \
            -> carscanner.service.FileBackupService:
        return carscanner.service.FileBackupService(car_offer_dao, vehicle_data_path_v3)

    def filter_dao(self, mem_db: tinydb.TinyDB) -> carscanner.dao.FilterDao:
        return carscanner.dao.FilterDao(mem_db)

    filter_svc = carscanner.service.FilterService

    @contextlib.contextmanager
    def mem_db(self) -> tinydb.TinyDB:
        db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
        try:
            yield db
        finally:
            db.close()

    def meta_col(self, mongodb_carscanner_db: pymongo.database.Database) -> pymongo.collection.Collection:
        from carscanner.dao.meta import META_V2
        return mongodb_carscanner_db.get_collection(META_V2, codec_options=mongodb_carscanner_db.codec_options)

    metadata_dao = carscanner.dao.MetadataDao

    def migration_service(self, mongodb_carscanner_db: pymongo.database.Database) \
            -> carscanner.service.migration.MigrationService:
        return carscanner.service.migration.MigrationService(
            mongodb_carscanner_db,
        )

    def mongodb_carscanner_db(self, mongodb_connection: pymongo.MongoClient) -> pymongo.database.Database:
        return mongodb_connection.get_database(codec_options=mongodb_connection.codec_options)

    def mongodb_connection(self) -> pymongo.MongoClient:
        import os
        return pymongo.MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost/carscanner'), retryWrites=False)

    offer_export_svc = carscanner.service.ExportService

    offers_svc = carscanner.service.OfferService

    @contextlib.contextmanager
    def static_data(self, config: Config) -> tinydb.TinyDB:
        import carscanner.dao.resources
        storage = carscanner.data.ResourceStorage
        storage = storage if config.modify_static else carscanner.data.ReadOnlyMiddleware(storage)
        db = tinydb.TinyDB(storage=storage, package=carscanner.dao.resources, resource='static.json', indent=2)
        try:
            yield db
        finally:
            db.close()

    def timestamp(self) -> int:
        return carscanner.utils.now()

    def token_col(self, mongodb_carscanner_db: pymongo.database.Database) -> pymongo.collection.Collection:
        return mongodb_carscanner_db.get_collection('token', codec_options=mongodb_carscanner_db.codec_options)

    token_store = carscanner.dao.MongoTrustStore

    def vehicle_collection_v4(self, mongodb_carscanner_db: pymongo.database.Database) -> pymongo.collection.Collection:
        from carscanner.dao.car_offer import VEHICLE_V3
        return mongodb_carscanner_db.get_collection(VEHICLE_V3, codec_options=mongodb_carscanner_db.codec_options)

    def vehicle_data_path_v3(self, ns: argparse.Namespace) -> pathlib.Path:
        from carscanner.dao.car_offer import VEHICLE_V3

        return ns.data / VEHICLE_V3

    def voivodeship_dao(self, static_data: tinydb.TinyDB) -> carscanner.dao.VoivodeshipDao:
        return carscanner.dao.VoivodeshipDao(static_data)

    voivodeship_svc = carscanner.service.VoivodeshipService
