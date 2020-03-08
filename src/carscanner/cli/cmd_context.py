from carscanner.cli.cmd_offers import OffersCommand
from carscanner.context import Context
from carscanner.utils import memoized


class CmdContext(Context):
    def __init__(self, ns):
        super().__init__()
        ns.data = ns.data.expanduser()
        self._ns = ns

    @property
    def data_path(self):
        return self._ns.data

    @property
    def environment(self):
        return self._ns.environment

    @property
    def ns(self):
        return self._ns

    @memoized
    def offers_cmd(self):
        return OffersCommand(
            self.offers_svc(),
            self.metadata_dao(),
            self.filter_svc(),
            self.offer_export_svc(),
            self.datetime_now(),
            self.data_path,
            self.file_backup_service(),
            self.executor(),
            self.ns.output,
        )

