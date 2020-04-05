import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

import carscanner.utils
from carscanner.service import GitBackupService


def setup_module():
    carscanner.utils.configure_logging()


class TestGitBackupService(TestCase):
    @patch('git.Repo')
    def test_backup(self, repo_mock):
        dao = Mock()
        dao.all = Mock(return_value=[])
        export_svc = Mock()

        with tempfile.TemporaryDirectory() as tmpDir:
            data_path = Path(tmpDir)
            export_path = data_path
            GitBackupService(dao, data_path, export_path, export_svc, 'remote_repo_uri',
                             export_path / 'vehicle').backup()

    @patch('git.Repo')
    def test_do_git_clone_pull(self, repo_mock):
        from carscanner.service.git_backup import do_git_clone
        log_q = Mock()
        with tempfile.TemporaryDirectory() as tmpDir:
            data_path = Path(tmpDir)
            do_git_clone('remote_repo_uri', data_path, log_q)

        repo_mock.assert_called_once_with(data_path)
        repo_mock().remote.assert_called_once_with('origin')
        log_q.put.assert_called_with('Git repo ready')

    @patch('git.Repo')
    def test_do_git_clone_clone(self, repo_mock):
        from carscanner.service.git_backup import do_git_clone
        log_q = Mock()
        data_path = Path(tempfile.mktemp())

        do_git_clone('remote_repo_uri', data_path, log_q)

        repo_mock.clone_from.assert_called_once_with('remote_repo_uri', data_path, depth=1)
        log_q.put.assert_called_with('Git repo ready')
