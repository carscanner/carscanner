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

commiter = git.Actor('CarScanner', 'carscanner@users.noreply.github.com')


def spawn_logging_thread(name: str, log_q):
    import threading

    def do_log(name: str, log_q: mp.Queue):
        while msg := log_q.get(True):
            if msg is StopIteration:
                break
            logging.getLogger(name).info(msg)

    log_t = threading.Thread(target=do_log, args=(name, log_q,), daemon=True)
    log_t.start()


def git_clone(uri: str, data_path: pathlib.Path, log_q: mp.Queue) -> typing.Optional[mp.Process]:
    if data_path.exists():
        return None

    def do_git_clone(uri: str, data_path: pathlib.Path, log_q: mp.Queue) -> None:
        import git
        log_q.put_nowait('Preparing git repo for backup')
        git.Repo.clone_from(uri, data_path, depth=1)
        log_q.put_nowait('Git repo ready')

    p = mp.Process(target=do_git_clone, args=(uri, data_path, log_q,))
    p.start()
    return p


def commit_push(repo_dir: pathlib.Path, log_q: mp.Queue) -> mp.Process:
    def do_commit_push(repo_dir: pathlib.Path, log_q: mp.Queue) -> None:
        r = git.Repo(repo_dir)
        idx = r.index

        log_q.put_nowait('Adding items to index')
        idx.add((str(f) for f in repo_dir.glob('**/*.json')), write=True)

        if len(idx.diff(r.head.commit)):
            from datetime import datetime
            log_q.put_nowait('Committing changes')
            idx.commit('Update for ' + datetime.today().isoformat(), author=commiter, commiter=commiter)

            log_q.put_nowait('Pushing backup repo')
            r.remote('origin').push()

    p = mp.Process(target=do_commit_push, args=(repo_dir, log_q,))
    p.start()
    return p


class GitBackupService(BackupService):
    def __init__(self, dao: CarOfferDao, data_path: pathlib.Path, uri: str):
        self._dao = dao
        self._data_path = data_path
        self._uri = uri

    def backup(self):
        log.info('Preparing backup')
        with tinydb.TinyDB(storage=tinydb.storages.MemoryStorage) as db, mp.Queue() as log_q:
            spawn_logging_thread('carscanner.__git__', log_q)

            clone_p = git_clone(self._uri, self._data_path, log_q)

            tbl: tinydb.database.Table = db.table(_VEHICLE_V3)
            tbl.insert_multiple(BackupService._convert(obj) for obj in self._dao.all())

            if clone_p:
                clone_p.join()

            VehicleShardLoader(tbl, self._data_path).close()

            commit_push(self._data_path, log_q).join()
            log_q.put(StopIteration)
