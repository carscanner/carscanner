import logging
import multiprocessing as mp
import pathlib
import typing

import git
import tinydb

from carscanner.dao import CarOfferDao
from carscanner.dao.car_offer import VEHICLE_V3 as _VEHICLE_V3
from carscanner.data import VehicleShardLoader
from carscanner.service.backup import BackupService

log = logging.getLogger(__name__)

committer = git.Actor('CarScanner', 'carscanner@users.noreply.github.com')


def spawn_logging_thread(name: str, log_q):
    import threading

    def do_log(name: str, log_q: mp.Queue):
        while msg := log_q.get(True):
            if msg is StopIteration:
                log_q.close()
                break
            logging.getLogger(name).info(msg)

    log_t = threading.Thread(target=do_log, args=(name, log_q,), daemon=True)
    log_t.start()
    return log_t


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
    def __init__(self, car_offer_dao: CarOfferDao, data_path: pathlib.Path, vehicle_data_path: pathlib.Path, uri: str):
        self._dao = car_offer_dao
        self._data_path = data_path
        self._vehicle_data_path = vehicle_data_path
        self._uri = uri

        self.log_q = None
        self.log_t = None
        self.clone_p = None

    def backup(self):
        log.info('Preparing backup')

        self.log_q = mp.Queue()
        self.log_t = spawn_logging_thread('carscanner.__git__', self.log_q)
        self.clone_p = git_clone(self._uri, self._data_path, self.log_q)

        with tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as db:
            tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
            tbl.insert_multiple(BackupService._convert(obj) for obj in self._dao.all())

            if self.clone_p:
                self.clone_p.join()

            VehicleShardLoader(tbl, self._vehicle_data_path).close()

        commit_push(self._data_path, self.log_q).join()
        self.log_q.put(StopIteration)
        self.log_t.join()
        log.info('Backup done')
