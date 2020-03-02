import argparse
import concurrent.futures as futures
import datetime
import json
import logging
import pathlib
import sys

import allegro_pl
import pymongo
import pymongo.database
import tinydb

import carscanner
import carscanner.allegro
import carscanner.dao
import carscanner.data
import carscanner.service
import carscanner.service.migration
from carscanner.utils import memoized, unix_to_datetime

log = logging.getLogger(__name__)

ENV_TRAVIS = 'travis'
ENV_LOCAL = 'local'


class Context:
    def __init__(self):
        self._ns = None
        self._modify_static = False
        self._closeables = []

    def close(self):
        for o in reversed(self._closeables):
            o.close()

    @property
    def ns(self):
        return self._ns

    @ns.setter
    def ns(self, ns):
        self._ns = ns

    @property
    def modify_static(self):
        return self._modify_static

    @modify_static.setter
    def modify_static(self, value: bool) -> None:
        self._modify_static = value

    @memoized
    def allegro(self):
        return carscanner.allegro.CarscannerAllegro(self.allegro_client())

    @memoized
    def datetime_now(self) -> datetime.datetime:
        return unix_to_datetime(self.timestamp())

    @memoized
    def mem_db(self):
        db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
        self._closeables.append(db)
        return db

    @memoized
    def filter_svc(self):
        return carscanner.service.FilterService(
            self.allegro(),
            self.filter_dao(),
            self.criteria_dao())

    @memoized
    def filter_dao(self):
        return carscanner.dao.FilterDao(self.mem_db())

    @memoized
    def car_offers_builder(self):
        return carscanner.service.CarOffersBuilder(self.voivodeship_dao(), self.car_makemodel_dao(),
                                                   self.datetime_now())

    @memoized
    def voivodeship_dao(self):
        return carscanner.dao.VoivodeshipDao(self.static_data())

    @memoized
    def criteria_dao(self):
        return carscanner.dao.CriteriaDao(self.static_data())

    @memoized
    def categories_svc(self):
        return carscanner.service.GetCategories(self.allegro(), self.criteria_dao())

    @memoized
    def car_makemodel_svc(self):
        return carscanner.service.CarMakeModelService(self.car_makemodel_dao())

    @memoized
    def car_makemodel_dao(self):
        return carscanner.dao.CarMakeModelDao(self.static_data())

    @memoized
    def timestamp(self):
        return carscanner.utils.now()

    @memoized
    def voivodeship_svc(self):
        return carscanner.service.VoivodeshipService(self.allegro(), self.voivodeship_dao())

    @memoized
    def offer_export_svc(self):
        return carscanner.service.ExportService(self.car_offer_dao(), self.metadata_dao())

    # ##### all changed methods from Context go here, ordered by name

    @memoized
    def allegro_auth(self):
        ts = carscanner.dao.MongoTrustStore(self.token_collection())
        if self.ns.environment == ENV_LOCAL:
            cs = carscanner.allegro.YamlClientCodeStore(carscanner.allegro.codes_path)
            allow_fetch = not self.ns.no_fetch
        elif self.ns.environment == ENV_TRAVIS:
            cs = carscanner.allegro.EnvironClientCodeStore()
            allow_fetch = False
        else:
            raise ValueError(self.ns.environment)
        return carscanner.allegro.CarScannerCodeAuth(cs, ts, allow_fetch)

    @memoized
    def allegro_client(self):
        return allegro_pl.Allegro(self.allegro_auth())

    @memoized
    def car_offer_dao(self):
        return carscanner.dao.CarOfferDao(self.vehicle_collection_v4())

    @memoized
    def file_backup_service(self):
        return carscanner.service.FileBackupService(self.car_offer_dao(), self.vehicle_data_path_v3())

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

    @memoized
    def mongodb_carscanner_db(self) -> pymongo.database.Database:
        conn = self.mongodb_connection()
        return conn.get_database(codec_options=conn.codec_options)

    @memoized
    def mongodb_connection(self) -> pymongo.MongoClient:
        import os
        return pymongo.MongoClient(os.environ.get('MONGODB_URI'), retryWrites=False)

    @memoized
    def offers_cmd(self):
        return OffersCommand(
            self.offers_svc(),
            self.metadata_dao(),
            self.filter_svc(),
            self.offer_export_svc(),
            self.datetime_now(),
            self.ns.data,
            self.file_backup_service(),
            self.executor(),
        )

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
        self._closeables.append(db)
        return db

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

        root_path: pathlib.Path = self.ns.data

        data_path = root_path / VEHICLE_V3
        return data_path

    @memoized
    def executor(self):
        executor = futures.ThreadPoolExecutor()

        def close(*_):
            futures.ThreadPoolExecutor.shutdown(executor, True)

        executor.close = close
        self._closeables.append(executor)
        return executor


class CommandLine:
    def __init__(self):
        self._context = Context()
        self._parser = self.build_parser()

    def build_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--data', '-d', default='.', type=pathlib.Path, metavar='dir',
                            help='Database directory. Default is %(default)s')
        parser.add_argument('--environment', '-e', default=ENV_LOCAL, choices=[ENV_LOCAL, ENV_TRAVIS], metavar='env',
                            help='Where to read client codes from. One of %(choices)s. Default is %(default)s')
        parser.add_argument('--no-fetch', '--nf', action='store_true', default=False,
                            help="Don't fetch token if it's expired")
        parser.add_argument('--version', '-v', action='version', version=carscanner.__version__)
        subparsers = parser.add_subparsers()

        for c in [
            CarListCommand,
            CriteriaCommand,
            FilterCommand,
            OffersCommand,
            TokenCommand,
            VoivodeshipCommand,
        ]:
            c.build_argparse(subparsers, self._context, parser.print_help)

        return parser

    def start(self):
        ns = self._parser.parse_args()
        ns.data = ns.data.expanduser()
        self._context.ns = ns

        log.info("Starting")

        self._context.migration_service().check_migrate()

        try:
            ns.func()
        except allegro_pl.TokenError as x:
            print('Invalid token, fetch disabled. Exiting', x.args)
            raise
        else:
            self._context.close()


class TokenCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, help_fn):
        token_parser = subparsers.add_parser('token', help='Manipulate security tokens')
        token_parser.set_defaults(func=help_fn)
        token_subparsers = token_parser.add_subparsers()

        token_refresh_parser = token_subparsers.add_parser('refresh', help='Refresh token')
        token_refresh_parser.set_defaults(func=lambda: ctx.allegro_auth().refresh_token())

        token_fetch_opt = token_subparsers.add_parser('fetch', help='Fetch token')
        token_fetch_opt.set_defaults(func=lambda: ctx.allegro_auth().fetch_token())


class CarListCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, print_help):
        carlist_cmd = subparsers.add_parser('carlist', help='Manipulate car makes & models list')
        carlist_cmd.set_defaults(func=print_help)
        carlist_subparsers = carlist_cmd.add_subparsers()

        def update():
            ctx.modify_static = True
            ctx.car_makemodel_svc().load_car_list(ctx.ns.input)

        carlist_update_cmd = carlist_subparsers.add_parser('update', help='Load car makes & models from json file to '
                                                                          'the database')
        carlist_update_cmd.set_defaults(func=update)
        carlist_update_cmd.add_argument('--input', '-i', type=pathlib.Path, help='Input json file', metavar='path')

        carlist_show_cmd = carlist_subparsers.add_parser('show')
        carlist_show_cmd.set_defaults(func=lambda: ctx.car_makemodel_svc().show_car_list())

    def __init__(self, service: carscanner.service.CarMakeModelService, input_file):
        self.input = input_file
        self._service = service

    def update(self):
        self._service.load_car_list(self.input)


class CriteriaCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, print_help):
        criteria_parser = subparsers.add_parser('criteria', aliases=['crit'], help='Manipulate criteria')
        criteria_parser.set_defaults(func=print_help)
        criteria_subparsers = criteria_parser.add_subparsers()

        def build():
            ctx.modify_static = True
            ctx.categories_svc().build_criteria()

        criteria_build_opt = criteria_subparsers.add_parser('build', help='Build criteria database')
        criteria_build_opt.set_defaults(func=build)


class OffersCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, print_help):
        offers_parser = subparsers.add_parser('offers', help='Manipulate offers')
        offers_parser.set_defaults(func=print_help)
        offers_subparsers = offers_parser.add_subparsers()

        offers_update_opt = offers_subparsers.add_parser('update', help='Update and export current offers')
        offers_update_opt.set_defaults(func=lambda: ctx.offers_cmd().update())

        offers_export_opt = offers_subparsers.add_parser('export')
        offers_export_opt.set_defaults(func=lambda: ctx.offer_export_svc().export(ctx.ns.data / ctx.ns.output))
        offers_export_opt.add_argument('--output', '-o', type=pathlib.Path, help='Output json file', metavar='path')

    def __init__(self,
                 offer_svc,
                 meta_dao,
                 filter_svc: carscanner.service.FilterService,
                 export_svc: carscanner.service.ExportService,
                 ts: datetime.datetime,
                 data_path: pathlib.Path,
                 backup_svc: carscanner.service.FileBackupService,
                 executor: futures.Executor,
                 ):
        self.ts = ts
        self.filter_svc = filter_svc
        self.meta_dao: carscanner.dao.MetadataDao = meta_dao
        self.offer_svc: carscanner.service.OfferService = offer_svc
        self._export_svc = export_svc
        self._data_path = data_path
        self._backup_service = backup_svc
        self._executor = executor

    def update(self):
        self.meta_dao.report()
        self.filter_svc.load_filters()
        self.offer_svc.get_offers()
        self.meta_dao.update(self.ts)
        self._executor.submit(self._export_svc.export, self._data_path / 'export.json')
        self._executor.submit(self._backup_service.backup)


class VoivodeshipCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, print_help):
        vs_parser = subparsers.add_parser('voivodeship', help='Manipulate voivodeship database')
        vs_parser.set_defaults(func=print_help)
        vs_subparsers = vs_parser.add_subparsers()

        def load():
            ctx.modify_static = True
            ctx.voivodeship_svc().load_voivodeships()

        vs_load_cmd = vs_subparsers.add_parser('load')
        vs_load_cmd.set_defaults(func=load)


class FilterCommand:
    @staticmethod
    def build_argparse(subparsers, ctx: Context, print_help):
        filter_parser = subparsers.add_parser('filter', help='Manipulate category filters')
        filter_parser.set_defaults(func=print_help)
        filter_subparsers = filter_parser.add_subparsers()

        filter_show_cmd: argparse.ArgumentParser = filter_subparsers.add_parser('get')
        filter_show_cmd.add_argument('--category', '-c', default='ALL', help='Category id. Default is all categories')
        filter_show_cmd.add_argument('--output', '-o', default='-', help='Output file. use - to output to the standard '
                                                                         'output (the default)')
        filter_show_cmd.set_defaults(func=lambda: FilterCommand.get(ctx))

    @staticmethod
    def get(ctx: Context):
        output_path = ctx.ns.output
        cat_id = ctx.ns.category

        def to_dict(o):
            return o.to_dict()

        try:
            if output_path == '-':
                output = sys.stdout
            else:
                output = open(output_path, 'wt')

            cat_ids = [cat_id] if cat_id != 'ALL' else [c.category_id for c in ctx.criteria_dao().all()]

            result = {cat_id: ctx.allegro().get_filters(cat_id) for cat_id in cat_ids}
            json.dump(result, output, default=to_dict, indent=2)
        finally:
            if output and output is not sys.stdout:
                output.close()


def main():
    carscanner.utils.configure_logging()
    CommandLine().start()


if __name__ == '__main__':
    main()
