from argparse import Namespace
from pathlib import Path

import allegro_pl

from carscanner.allegro import codes_path, EnvironClientCodeStore, YamlClientCodeStore
from carscanner.context import ENV_LOCAL, ENV_TRAVIS
from carscanner.service import FileBackupService


class CmdContext:
    def __init__(self, ns: Namespace):
        self._ns = ns

    def client_code_store(self) -> allegro_pl.ClientCodeStore:
        if self._ns.environment == ENV_LOCAL:
            return YamlClientCodeStore(codes_path)
        elif self._ns.environment == ENV_TRAVIS:
            return EnvironClientCodeStore()
        else:
            raise ValueError(self._ns.environment)

    backup_svc = FileBackupService

    def data_path(self) -> Path:
        result = Path(self._ns.data).expanduser()
        result.mkdir(parents=True, exist_ok=True)
        return result

    def export_path(self, data_path: Path) -> Path:
        export_name = self._ns.output if 'output' in self._ns else 'export.json'
        return data_path / export_name
