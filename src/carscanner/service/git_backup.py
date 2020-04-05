import contextlib
import logging
import multiprocessing as mp
import pathlib
import typing

import git
import tinydb

from carscanner.dao import CarOfferDao
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from carscanner.data import VehicleShardLoader
from carscanner.service import BackupService, ExportService

log = logging.getLogger(__name__)

committer = git.Actor('CarScanner', 'carscanner@users.noreply.github.com')


@contextlib.contextmanager
def spawn_logging_thread(name: str) -> mp.Queue:
    import threading

    def do_log(name: str, log_q: mp.Queue):
        while msg := log_q.get(True):
            if msg is StopIteration:
                log_q.close()
                break
            logging.getLogger(name).info(msg)

    log_q = mp.Queue()
    log_t = threading.Thread(target=do_log, args=(name, log_q,), daemon=True)
    log_t.start()
    try:
        yield log_q
    finally:
        log_q.put(StopIteration)
        log_t.join()


def do_git_clone(uri: str, data_path: pathlib.Path, log_q: mp.Queue) -> None:
    log_q.put('Preparing git repo for backup')

    try:
        if data_path.exists():
            git.Repo(data_path).remote('origin').pull()
        else:
            git.Repo.clone_from(uri, data_path, depth=1)
    except BaseException as e:
        log_q.put(str(e))
    else:
        log_q.put('Git repo ready')


def git_clone(uri: str, data_path: pathlib.Path, log_q: mp.Queue) -> typing.Optional[mp.Process]:
    p = mp.Process(target=do_git_clone, args=(uri, data_path, log_q,))
    p.start()
    return p


def do_commit_push(repo_dir: pathlib.Path, log_q: mp.Queue) -> None:
    try:
        r = git.Repo(repo_dir)
        idx = r.index

        log_q.put_nowait('Adding items to index')
        idx.add((str(f) for f in repo_dir.rglob('*.json')), write=True)

        if len(idx.diff(r.head.commit)):
            from datetime import datetime
            log_q.put_nowait('Committing changes')
            idx.commit(f'Update for {datetime.today().isoformat()}', author=committer, committer=committer)

            log_q.put_nowait('Pushing backup repo')
            r.remote('origin').push()
            log_q.put_nowait('Push done')
    except BaseException as e:
        log_q.put(str(e))


def commit_push(repo_dir: pathlib.Path, log_q: mp.Queue) -> mp.Process:
    p = mp.Process(target=do_commit_push, args=(repo_dir, log_q,))
    p.start()
    return p


class GitBackupService(BackupService):
    def __init__(
            self,
            car_offer_dao: CarOfferDao,
            data_path: pathlib.Path,
            export_path: pathlib.Path,
            offer_export_svc: ExportService,
            backup_remote: str,
            vehicle_data_path_v3: pathlib.Path,
    ):
        self._car_offer_dao = car_offer_dao
        self._data_path = data_path
        self._export_path = export_path
        self._offer_export_svc = offer_export_svc
        self._uri = backup_remote
        self._vehicle_data_path = vehicle_data_path_v3

    def backup(self):
        log.info('Preparing backup')

        with tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as db, \
                spawn_logging_thread('carscanner.__git__') as log_q:
            clone_p = git_clone(self._uri, self._data_path, log_q)

            tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
            tbl.insert_multiple(BackupService._convert(obj) for obj in self._car_offer_dao.all())

            clone_p.join()

            self._offer_export_svc.export(self._export_path)
            VehicleShardLoader(tbl, self._vehicle_data_path).close()

            commit_push(self._data_path, log_q).join()
        log.info('Backup done')
