"""Run sequential CPU training parts and periodically export a local voice preview."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs'
STAGES = ('acoustic', 'vocoder')
PYTHON = sys.executable
REVIEW = ROOT / 'outputs/training-review'


def load_steps():
    # Read checkpoint metadata outside the runner to keep its memory footprint small.
    code = """
import json
from pathlib import Path
import torch
steps = {}
for stage in ('acoustic', 'vocoder'):
    path = Path('runs') / stage / 'last.pt'
    state = torch.load(path, mmap=True, map_location='cpu', weights_only=False) if path.exists() else None
    if state is not None and state['stage'] != stage:
        raise ValueError(f'{path} contains the wrong stage')
    steps[stage] = state['step'] if state is not None else 0
print(json.dumps(steps))
"""
    return json.loads(subprocess.check_output([PYTHON, '-c', code], cwd=ROOT, text=True))


def choose_part(steps, targets, warmup, size):
    available = [stage for stage in STAGES if steps[stage] < targets[stage]]
    if not available:
        return None
    if steps['vocoder'] < min(warmup, targets['vocoder']):
        return 'vocoder', min(size, warmup - steps['vocoder'], targets['vocoder'] - steps['vocoder'])
    stage = min(available, key=lambda name: steps[name] / targets[name])
    return stage, min(size, targets[stage] - steps[stage])


def critical_memory():
    if sys.platform != 'darwin':
        return False
    try:
        level = subprocess.check_output(
            ['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
        )
        return int(level) >= 4
    except (OSError, subprocess.SubprocessError, ValueError):
        return False


class Runner:
    def __init__(self):
        self.stopping = False
        self.child = None

    def stop(self, signum, frame):
        self.stopping = True
        if self.child is not None and self.child.poll() is None:
            self.child.send_signal(signal.SIGTERM)

    def command(self, script, *args):
        if self.stopping:
            return None
        self.child = subprocess.Popen(
            [PYTHON, '-u', f'scripts/{script}', *args], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        last = None
        try:
            if self.stopping:
                self.child.send_signal(signal.SIGTERM)
            for line in self.child.stdout:
                print(line, end='', flush=True)
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        last = row
                except json.JSONDecodeError:
                    pass
            code = self.child.wait()
            if code and not self.stopping:
                raise RuntimeError(f'{script} exited with code {code}')
            return last
        finally:
            self.child.stdout.close()
            self.child = None

    def preview(self, steps):
        a, v = steps['acoustic'], steps['vocoder']
        if not a or not v or self.stopping:
            return
        key = f'acoustic-acoustic-{a:07d}-v{v:07d}'
        folder = REVIEW / key
        if (folder / 'model/model.json').is_file():
            return
        index = REVIEW / 'index.json'
        rows = json.loads(index.read_text()) if index.is_file() else []
        if not any(row['id'] == key for row in rows):
            self.command('export_review.py', '--stage', 'acoustic', '--run', 'runs/acoustic', '--pair-id')
        self.command('export_browser.py', '--review-id', key)


def status(state, **parts):
    path = RUNS / 'continuous-status.json'
    partial = path.with_suffix('.tmp')
    partial.write_text(json.dumps({
        'status': state, 'updated_utc': datetime.now(timezone.utc).isoformat(), **parts,
    }, indent=2) + '\n')
    partial.replace(path)
    print(json.dumps({'schedule': state, **parts}), flush=True)


def run(args):
    cfg = json.loads((ROOT / 'configs/oddmouth.json').read_text())
    targets = {stage: cfg['training'][stage]['total_steps'] for stage in STAGES}
    warmup = cfg['training']['vocoder']['adversarial_start_step']
    reserve = cfg['storage']['minimum_free_disk_bytes']
    runner = Runner()
    signal.signal(signal.SIGINT, runner.stop)
    signal.signal(signal.SIGTERM, runner.stop)
    steps = load_steps()
    last_preview = -args.preview_interval

    while not runner.stopping:
        if shutil.disk_usage(RUNS).free < reserve + 500_000_000:
            raise RuntimeError('Training stopped to preserve the configured free disk reserve')
        if critical_memory():
            status('waiting_for_memory', steps=steps, targets=targets)
            for _ in range(30):
                if runner.stopping:
                    break
                time.sleep(1)
            continue
        part = choose_part(steps, targets, warmup, args.chunk_steps)
        if sum(steps.values()) - last_preview >= args.preview_interval or part is None:
            status('exporting_preview', steps=steps, targets=targets)
            try:
                runner.preview(steps)
            except RuntimeError as error:
                print(f'Preview export failed: {error}', flush=True)
                if part is None:
                    raise
            last_preview = sum(steps.values())
        if part is None:
            if not runner.stopping:
                status('finished', steps=steps, targets=targets)
            break
        if runner.stopping:
            break
        stage, count = part
        status('training', stage=stage, part_steps=count, steps=steps, targets=targets)
        result = runner.command(
            'train.py', '--stage', stage, '--device', 'cpu', '--steps', str(count),
            '--minutes', str(args.minutes_per_part), '--log-every', '50',
            '--eval-every', str(args.preview_interval), '--run', f'runs/{stage}',
        )
        if result and 'saved' in result and 'step' in result:
            previous = steps[stage]
            steps[stage] = result['step']
            if steps[stage] <= previous and not runner.stopping:
                raise RuntimeError('Training did not advance the checkpoint')
        elif not runner.stopping:
            raise RuntimeError('Trainer exited without confirming a saved checkpoint')

    if runner.stopping:
        status('stopped', steps=steps, targets=targets)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chunk-steps', type=int, default=1000)
    parser.add_argument('--minutes-per-part', type=float, default=5)
    parser.add_argument('--preview-interval', type=int, default=5000)
    args = parser.parse_args()
    if min(args.chunk_steps, args.minutes_per_part, args.preview_interval) <= 0:
        parser.error('Part and preview limits must be positive')
    RUNS.mkdir(exist_ok=True)
    with (RUNS / '.continuous.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another training schedule is live')
        run(args)


if __name__ == '__main__':
    main()
