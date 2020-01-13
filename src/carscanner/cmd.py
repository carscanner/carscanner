import argparse
import datetime
import json
import pathlib
import sys

import allegro_pl
import tinydb

import carscanner
import carscanner.allegro
import carscanner.dao
import carscanner.data
import carscanner.service
import carscanner.service.migration
from carscanner.utils import memoized, unix_to_datetime

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
    def auth(self):
        ts = carscanner.allegro.InsecureTokenStore(self.ns.data / 'tokens.yaml')
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
    def allegro(self):
        return carscanner.allegro.CarscannerAllegro(self.allegro_client())

    @memoized
    def datetime_now(self) -> datetime.datetime:
        return unix_to_datetime(self.timestamp())

    @memoized
    def offers_cmd(self):
        return OffersCommand(self.offers_svc(), self.metadata_dao(), self.filter_svc(), self.offer_export_svc(),
                             self.datetime_now(), self.ns.data)

    @memoized
    def mem_db(self):
        db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
        self._closeables.append(db)
        return db

    @memoized
    def offers_svc(self):
        return carscanner.service.OfferService(
            self.allegro(),
            self.criteria_dao(),
            self.car_offers_builder(),
            self.car_offer_dao(),
            self.filter_svc(),
            self.metadata_dao(),
            self.datetime_now()
        )

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
    def allegro_client(self):
        return allegro_pl.Allegro(self.auth())

    @memoized
    def offer_export_svc(self):
        return carscanner.service.ExportService(self.car_offer_dao(), self.metadata_dao())

    # ##### all changed methods from Context go here, ordered by name

    @memoized
    def car_offer_dao(self):
        return carscanner.dao.CarOfferDao(self.cars_db_v2())

    @memoized
    def cars_db_v1(self):
        db = tinydb.TinyDB(self.ns.data / 'cars.json', indent=2)
        self._closeables.append(db)
        return db

    @memoized
    def cars_db_v2(self) -> tinydb.TinyDB:
        db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)

        from carscanner.dao.car_offer import VEHICLE_V3

        loader = carscanner.data.VehicleShardLoader(db.table(VEHICLE_V3), self.vehicle_data_path())
        loader.load()

        self._closeables.append(db)
        self._closeables.append(loader)

        return db

    @memoized
    def migrate_aws(self):
        from carscanner.service.migration_aws.dynamodb import MigrateAWS
        from carscanner.dao.car_offer import VEHICLE_V3
        return MigrateAWS(self.cars_db_v2().table(VEHICLE_V3))

    @memoized
    def metadata_dao(self):
        return carscanner.dao.MetadataDao(self.cars_db_v1())

    @memoized
    def migration_service(self):
        return carscanner.service.migration.MigrationService(self.cars_db_v1(), self.cars_db_v2(), self.migration_v2(),
                                                             self.migration_v3())

    @memoized
    def migration_v2(self):
        return carscanner.service.migration.MigrationV2(self.cars_db_v1())

    @memoized
    def migration_v3(self):
        return carscanner.service.migration.MigrationV3(self.cars_db_v1(), self.cars_db_v2(), self.ns.data)

    @memoized
    def static_data(self) -> tinydb.TinyDB:
        storage = tinydb.TinyDB.DEFAULT_STORAGE if self.modify_static else carscanner.data.ReadOnlyMiddleware()
        db = tinydb.TinyDB(storage=storage, path=self.ns.data / 'static.json', indent=2)
        self._closeables.append(db)
        return db

    @memoized
    def vehicle_data_path(self) -> pathlib.Path:
        from carscanner.dao.car_offer import VEHICLE_V3

        root_path: pathlib.Path = self.ns.data

        data_path = root_path / VEHICLE_V3
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path


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
            MigrateCommand,
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

        self._context.migration_service().check_migrate()
        self._context.metadata_dao().post_init()

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
        token_refresh_parser.set_defaults(func=lambda: ctx.auth().refresh_token())

        token_fetch_opt = token_subparsers.add_parser('fetch', help='Fetch token')
        token_fetch_opt.set_defaults(func=lambda: ctx.auth().fetch_token())


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


class MigrateCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, _):
        migrate_parser: argparse.ArgumentParser = subparsers.add_parser('migrate', help='Migrate data to AWS DynamoDB')
        migrate_parser.set_defaults(func=migrate_parser.print_help)
        migrate_subparsers = migrate_parser.add_subparsers()

        run_parser = migrate_subparsers.add_parser('run')
        run_parser.add_argument('--profile', '-p', help='aws configuration profile', metavar='profile')
        run_parser.add_argument('--endpoint', '-e', help='Connection URL', metavar='endpoint')

        run_parser.set_defaults(func=lambda: ctx.migrate_aws().run(ctx.ns.profile, ctx.ns.endpoint))


class OffersCommand:
    @staticmethod
    def build_argparse(subparsers, ctx, print_help):
        offers_parser = subparsers.add_parser('offers', help='Manipulate offers')
        offers_parser.set_defaults(func=print_help)
        offers_subparsers = offers_parser.add_subparsers()

        offers_update_opt = offers_subparsers.add_parser('update', help='Update and export current offers')
        offers_update_opt.set_defaults(func=lambda: ctx.offers_cmd().update())

        offers_export_opt = offers_subparsers.add_parser('export')
        offers_export_opt.set_defaults(func=lambda: ctx.offer_export_svc().export(ctx.ns.output))
        offers_export_opt.add_argument('--output', '-o', type=pathlib.Path, help='Output json file', metavar='path')

    def __init__(self, offer_svc, meta_dao, filter_svc: carscanner.service.FilterService,
                 export_svc: carscanner.service.ExportService, ts: datetime.datetime, data_path: pathlib.Path):
        self.ts = ts
        self.filter_svc = filter_svc
        self.meta_dao: carscanner.dao.MetadataDao = meta_dao
        self.offer_svc: carscanner.service.OfferService = offer_svc
        self._export_svc = export_svc
        self._data_path = data_path

    def update(self):
        self.meta_dao.report()
        self.filter_svc.load_filters()
        self.offer_svc.get_offers()
        self.meta_dao.update(self.ts)
        export_path = self._data_path / 'export.json'
        self._export_svc.export(export_path)


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
