import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oddmouth.backup import Backup  # noqa: E402


class FakeHub:
    """Stands in for huggingface_hub.HfApi, storing files in a folder."""

    def __init__(self, store, private=True):
        self.store, self.private, self.uploads = Path(store), private, 0

    def create_repo(self, repo, private, exist_ok):
        assert private
        return SimpleNamespace(repo_id=f'someone/{repo}')

    def repo_info(self, repo):
        return SimpleNamespace(private=self.private)

    def list_repo_files(self, repo):
        return [str(p.relative_to(self.store)) for p in self.store.rglob('*') if p.is_file()]

    def hf_hub_download(self, repo, name, local_dir):
        target = Path(local_dir) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.store / name, target)

    def upload_folder(self, repo_id, folder_path, commit_message):
        self.uploads += 1
        shutil.copytree(folder_path, self.store, dirs_exist_ok=True)

    def super_squash_history(self, repo, commit_message):
        pass


def save(path, stage, step):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({'stage': stage, 'step': step, 'model': {}}, path)


class BackupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.hub = FakeHub(self.tmp / 'hub')
        (self.tmp / 'hub').mkdir()

    def test_push_uploads_only_changed_checkpoints(self):
        runs = self.tmp / 'runs'
        save(runs / 'acoustic/last.pt', 'acoustic', 100)
        (runs / 'acoustic/metrics.jsonl').write_text('{}\n')
        backup = Backup('repo', api=self.hub)
        self.assertEqual(backup.repo, 'someone/repo')
        self.assertEqual(backup.push(runs, ('acoustic', 'vocoder'), self.tmp / 'stage'), {'acoustic': 100})
        self.assertEqual(backup.push(runs, ('acoustic', 'vocoder'), self.tmp / 'stage'), {})
        self.assertEqual(self.hub.uploads, 1)
        save(runs / 'acoustic/last.pt', 'acoustic', 200)
        os.utime(runs / 'acoustic/last.pt', ns=(1, 1))
        self.assertEqual(backup.push(runs, ('acoustic', 'vocoder'), self.tmp / 'stage'), {'acoustic': 200})
        self.assertTrue((self.tmp / 'hub/acoustic/metrics.jsonl').exists())

    def test_restore_downloads_backed_up_stages(self):
        save(self.tmp / 'hub/vocoder/last.pt', 'vocoder', 50)
        found = Backup('repo', api=self.hub).restore(self.tmp / 'restore', ('acoustic', 'vocoder'))
        self.assertEqual(found, ['vocoder'])
        self.assertEqual(torch.load(self.tmp / 'restore/vocoder/last.pt')['step'], 50)

    def test_refuses_public_repository(self):
        with self.assertRaises(RuntimeError):
            Backup('repo', api=FakeHub(self.tmp / 'hub', private=False))


if __name__ == '__main__':
    unittest.main()
