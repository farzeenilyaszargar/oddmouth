"""Copy training checkpoints to a private Hugging Face model repository.

Cloud notebooks (for example Kaggle) can discard all output when a session is
stopped, so the cloud runner pushes each stage's last.pt here every so often
and restores the newest copy at the start of the next session.

The repository is created private and the backup refuses to write to a public
one: weights trained on DailyTalk must not be published.
"""
from pathlib import Path
import shutil

import torch

FILES = ('last.pt', 'metrics.jsonl')


def checkpoint_step(path):
    return torch.load(path, mmap=True, map_location='cpu', weights_only=False)['step']


class Backup:
    def __init__(self, repo, token=None, api=None):
        if api is None:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
        self.api = api
        self.repo = api.create_repo(repo, private=True, exist_ok=True).repo_id
        if not api.repo_info(self.repo).private:
            raise RuntimeError(f'{self.repo} is public; checkpoint backups need a private repository')
        self.pushed = {}

    def restore(self, dest, stages):
        """Download each stage's backed-up last.pt into dest/<stage>/; return the stages found."""
        present = set(self.api.list_repo_files(self.repo))
        found = []
        for stage in stages:
            name = f'{stage}/last.pt'
            if name in present:
                self.api.hf_hub_download(self.repo, name, local_dir=str(dest))
                found.append(stage)
        return found

    def push(self, runs, stages, staging):
        """Upload checkpoints that changed since the last push. Returns {stage: step} uploaded."""
        staging = Path(staging)
        shutil.rmtree(staging, ignore_errors=True)
        uploaded = {}
        for stage in stages:
            source = Path(runs) / stage / 'last.pt'
            if not source.exists():
                continue
            stamp = source.stat().st_mtime_ns
            if self.pushed.get(stage) == stamp:
                continue
            (staging / stage).mkdir(parents=True)
            # train.py replaces last.pt atomically, so this copy is always a whole checkpoint.
            for name in FILES:
                if (Path(runs) / stage / name).exists():
                    shutil.copy2(Path(runs) / stage / name, staging / stage / name)
            uploaded[stage] = (checkpoint_step(staging / stage / 'last.pt'), stamp)
        if not uploaded:
            return {}
        message = ', '.join(f'{stage} {step}' for stage, (step, _) in uploaded.items())
        self.api.upload_folder(repo_id=self.repo, folder_path=str(staging), commit_message=message)
        for stage, (_, stamp) in uploaded.items():
            self.pushed[stage] = stamp
        try:
            # Keep only the newest files so repeated 100 MB uploads don't pile up in storage.
            self.api.super_squash_history(self.repo, commit_message=f'Latest: {message}')
        except Exception as error:  # squashing only saves space; the upload already succeeded
            print(f'[backup] could not squash history: {error}', flush=True)
        shutil.rmtree(staging, ignore_errors=True)
        return {stage: step for stage, (step, _) in uploaded.items()}
