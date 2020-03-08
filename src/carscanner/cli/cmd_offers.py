import datetime
import pathlib
from concurrent import futures

import carscanner.dao
import carscanner.service


class OffersCommand:
    @staticmethod
    def build_argparse(subparsers):
        offers_parser = subparsers.add_parser('offers', help='Manipulate offers')
        offers_parser.set_defaults(func=lambda _: offers_parser.print_help())
        offers_subparsers = offers_parser.add_subparsers()

        offers_update_opt = offers_subparsers.add_parser('update', help='Update and export current offers')
        offers_update_opt.set_defaults(func=lambda ctx: ctx.offers_cmd().update())

        offers_export_opt = offers_subparsers.add_parser('export')
        offers_export_opt.set_defaults(func=lambda ctx: ctx.offer_export_svc().export(ctx.data_path / ctx.ns.output))
        offers_export_opt.add_argument('--output', '-o', type=pathlib.Path, help='Output json file', metavar='path',
                                       default='export.json')

    def __init__(self,
                 offer_svc,
                 meta_dao,
                 filter_svc: carscanner.service.FilterService,
                 export_svc: carscanner.service.ExportService,
                 ts: datetime.datetime,
                 data_path: pathlib.Path,
                 backup_svc: carscanner.service.FileBackupService,
                 executor: futures.Executor,
                 output_path: pathlib.Path,
                 ):
        self.ts = ts
        self.filter_svc = filter_svc
        self.meta_dao: carscanner.dao.MetadataDao = meta_dao
        self.offer_svc: carscanner.service.OfferService = offer_svc
        self._export_svc = export_svc
        self._data_path = data_path
        self._backup_service = backup_svc
        self._executor = executor
        self._output_path = data_path / output_path

    def update(self):
        self.meta_dao.report()
        self.filter_svc.load_filters()
        self.offer_svc.get_offers()
        self.meta_dao.update(self.ts)
        self._executor.submit(self._export_svc.export, self._output_path)
        self._executor.submit(self._backup_service.backup)
