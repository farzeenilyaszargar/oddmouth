"""Train both Oddmouth stages at once on a cloud CUDA machine (for example Kaggle).

    python scripts/train_cloud.py --hours 11 --runs /kaggle/working/runs --resume-from /kaggle/input

The acoustic model and the vocoder train in two processes. With two GPUs each
stage gets its own; with one GPU they share it. Each run continues from
<runs>/<stage>/last.pt. If that file is missing, the <stage>/last.pt with the
most steps under --resume-from (an uploaded Kaggle dataset or a previous
session's output) is copied in first. Both trainers save every 10 minutes and before --hours runs out.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('acoustic', 'vocoder')


def find_checkpoint(root, stage):
    """The <stage>/last.pt under root with the most training steps."""
    import torch
    if root is None or not root.exists():
        return None
    best, best_step = None, -1
    for path in root.rglob('last.pt'):
        if path.parent.name != stage:
            continue
        state = torch.load(path, mmap=True, map_location='cpu', weights_only=False)
        if state.get('stage') == stage and state['step'] > best_step:
            best, best_step = path, state['step']
    return best


def stream(prefix, process):
    for line in process.stdout:
        print(f'[{prefix}] {line}', end='', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--hours', type=float, default=11.0, help='Training time before both stages save and stop')
    parser.add_argument('--runs', type=Path, default=ROOT / 'runs')
    parser.add_argument('--data', type=Path, default=ROOT / 'data/dailytalk')
    parser.add_argument('--resume-from', type=Path, default=None, help='Folder searched for <stage>/last.pt')
    parser.add_argument('--stages', nargs='+', choices=STAGES, default=list(STAGES))
    parser.add_argument('--eval-every', type=int, default=2000, help='Steps between held-out evaluations and samples')
    args = parser.parse_args()

    import torch
    gpus = torch.cuda.device_count()
    if gpus == 0:
        parser.error('No CUDA GPU found. On Kaggle, set Accelerator to a GPU.')

    processes = []
    for index, stage in enumerate(args.stages):
        run = args.runs / stage
        run.mkdir(parents=True, exist_ok=True)
        if not (run / 'last.pt').exists():
            source = find_checkpoint(args.resume_from, stage)
            if source is not None:
                shutil.copy2(source, run / 'last.pt')
                print(f'[{stage}] resuming from {source}', flush=True)
            else:
                print(f'[{stage}] no checkpoint found; starting from random weights', flush=True)
        env = {**os.environ, 'CUDA_VISIBLE_DEVICES': str(index % gpus), 'PYTHONUNBUFFERED': '1'}
        command = [sys.executable, '-u', str(ROOT / 'scripts/train.py'), '--stage', stage,
                   '--device', 'cuda', '--cpu-share', str(round(1 / len(args.stages), 2)),
                   '--minutes', str(args.hours * 60), '--run', str(run), '--data', str(args.data),
                   '--log-every', '100', '--eval-every', str(args.eval_every)]
        process = subprocess.Popen(command, cwd=ROOT, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        thread = threading.Thread(target=stream, args=(stage, process), daemon=True)
        thread.start()
        processes.append((stage, process, thread))
        print(f'[{stage}] started on GPU {index % gpus} of {gpus}', flush=True)

    failed = []
    try:
        for stage, process, thread in processes:
            if process.wait():
                failed.append(stage)
            thread.join()
    except KeyboardInterrupt:
        for _, process, _ in processes:
            process.terminate()
        for _, process, _ in processes:
            process.wait()
    if failed:
        sys.exit(f'Training failed for: {", ".join(failed)}')


if __name__ == '__main__':
    main()
