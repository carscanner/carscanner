import os
import pathlib

import carscanner.allegro
import carscanner.service


class HerokuContext:
    def __init__(self):
        self.backup_remote = os.environ['BACKUP_REMOTE']
        self.data_path = pathlib.Path(os.environ['DATA_PATH']).expanduser()

    backup_svc = carscanner.service.GitBackupService

    client_code_store = carscanner.allegro.EnvironClientCodeStore

    def export_path(self, data_path: pathlib.Path) -> pathlib.Path:
        return data_path / 'export.json'
