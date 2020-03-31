import os
import pathlib

import carscanner.allegro
import carscanner.dao
import carscanner.service


class HerokuContext:
    def __init__(self):
        self.backup_remote = os.environ['BACKUP_REMOTE']
        self.data_path = pathlib.Path(os.environ['DATA_PATH']).expanduser()

    def backup_svc(
            self,
            car_offer_dao: carscanner.dao.CarOfferDao,
            data_path: pathlib.Path,
            vehicle_data_path_v3: pathlib.Path,
            backup_remote: str
    ) -> carscanner.service.GitBackupService:
        return carscanner.service.GitBackupService(car_offer_dao, data_path, vehicle_data_path_v3, backup_remote)

    client_code_store = carscanner.allegro.EnvironClientCodeStore

    def export_path(self, data_path: pathlib.Path) -> pathlib.Path:
        return data_path / 'export.json'
