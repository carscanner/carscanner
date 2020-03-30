import argparse
import datetime
import pathlib
from concurrent import futures

import carscanner.dao
import carscanner.service
import carscanner.context


class OffersCommand:
    @staticmethod
    def build_argparse(subparsers):
        offers_parser = subparsers.add_parser('offers', help='Manipulate offers')
        offers_parser.set_defaults(func=lambda _: offers_parser.print_help())
        offers_subparsers = offers_parser.add_subparsers()

        offers_update_opt = offers_subparsers.add_parser('update', help='Update and export current offers')
        offers_update_opt.set_defaults(func=lambda ctx: ctx.offers_cmd.update())
        offers_update_opt.add_argument('--output', '-o', type=pathlib.Path, help='Output json file', metavar='path',
                                       default='export.json')

        offers_export_opt = offers_subparsers.add_parser('export')
        offers_export_opt.set_defaults(func=lambda ctx: ctx.offer_export_svc.export(ctx.ns.data / ctx.ns.output))
        offers_export_opt.add_argument('--output', '-o', type=pathlib.Path, help='Output json file', metavar='path',
                                       default='export.json')

        offers_backup_opt = offers_subparsers.add_parser('backup')
        offers_backup_opt.set_defaults(func=lambda ctx: ctx.file_backup_service.backup())

    def __init__(self,
                 offers_svc: carscanner.service.OfferService,
                 metadata_dao: carscanner.dao.MetadataDao,
                 filter_svc: carscanner.service.FilterService,
                 offer_export_svc: carscanner.service.ExportService,
                 datetime_now: datetime.datetime,
                 file_backup_service: carscanner.service.FileBackupService,
                 executor: futures.Executor,
                 ns: argparse.Namespace,
                 ):
        self.ts = datetime_now
        self.filter_svc = filter_svc
        self.meta_dao = metadata_dao
        self.offer_svc = offers_svc
        self._export_svc = offer_export_svc
        self._data_path = ns.data
        self._backup_service = file_backup_service
        self._executor = executor
        self._output_path = ns.data / ns.output

    def update(self):
        self.meta_dao.report()
        self.filter_svc.load_filters()
        self.offer_svc.get_offers()
        self.meta_dao.update(self.ts)
        self._executor.submit(self._export_svc.export, self._output_path)
        self._executor.submit(self._backup_service.backup)
