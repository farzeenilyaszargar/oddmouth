"""Train one Oddmouth stage on a Mac or a CUDA GPU. Resumable; safe to stop with Ctrl-C.

    uv run python scripts/train.py --stage acoustic --minutes 60
    uv run python scripts/train.py --stage vocoder --minutes 60

Run one stage per process. Each run continues from runs/<stage>/last.pt if
present, saves every few minutes and on Ctrl-C, and writes listening samples
to runs/<stage>/samples/. All weights start random; nothing pretrained loads.
"""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import random
import signal
import shutil
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oddmouth.audio import HOP, SR, mel_spectrogram  # noqa: E402
from oddmouth.data import collate, frame_batches, load_acoustic, load_waves  # noqa: E402
from oddmouth.model import AcousticModel, Discriminators, Vocoder, count  # noqa: E402
from oddmouth.text import SYMBOL_VERSION, VOCAB_SIZE  # noqa: E402
from oddmouth.throttle import CpuLimiter, limit_threads  # noqa: E402


def write_wav(path, wave):
    from scipy.io import wavfile
    path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(path, SR, (wave.detach().float().cpu().clamp(-1, 1).numpy() * 32767).astype(np.int16))


def save_checkpoint(path, state, reserve):
    estimate = sum(v.numel() * v.element_size() for v in _tensors(state))
    if shutil.disk_usage(path.parent).free < reserve + 2 * estimate:
        raise RuntimeError('Not enough free disk to save while keeping the reserve')
    partial = path.with_suffix('.partial')
    torch.save(state, partial)
    os.replace(partial, path)


def _tensors(obj):
    if torch.is_tensor(obj):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _tensors(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _tensors(v)


def schedule(warmup, total, floor=0.1):
    def factor(step):
        if step < warmup:
            return (step + 1) / warmup
        progress = min(1.0, (step - warmup) / max(1, total - warmup))
        return floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * progress))
    return factor


def sync(device):
    if device.type == 'mps':
        torch.mps.synchronize()
    elif device.type == 'cuda':
        torch.cuda.synchronize(device)


def memory(device):
    if device.type == 'mps':
        return torch.mps.current_allocated_memory()
    if device.type == 'cuda':
        return torch.cuda.memory_allocated(device)
    return None


def host_memory_mb():
    """This process's resident memory and the machine's available memory, in MB (Linux only)."""
    try:
        status = Path('/proc/self/status').read_text()
        rss = int(next(line for line in status.splitlines() if line.startswith('VmRSS:')).split()[1])
        info = Path('/proc/meminfo').read_text()
        available = int(next(line for line in info.splitlines() if line.startswith('MemAvailable:')).split()[1])
        return {'host_rss_mb': rss // 1024, 'host_available_mb': available // 1024}
    except (OSError, StopIteration, ValueError):
        return {}


def discriminator_loss(real, fake):
    return sum((r[0] - 1).square().mean() + f[0].square().mean() for r, f in zip(real, fake)) / len(real)


def generator_losses(real, fake):
    adversarial = sum((f[0] - 1).square().mean() for f in fake) / len(fake)
    pairs = [(a, b) for (_, ra), (_, fa) in zip(real, fake) for a, b in zip(ra, fa)]
    matching = sum(F.l1_loss(b, a.detach()) for a, b in pairs) / len(pairs)
    return adversarial, matching


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stage', choices=['acoustic', 'vocoder'], required=True)
    parser.add_argument('--minutes', type=float, default=None, help='Stop and save after this long')
    parser.add_argument('--steps', type=int, default=None, help='Stop after this many more updates')
    parser.add_argument('--run', type=Path, default=None, help='Default: runs/<stage>')
    parser.add_argument('--data', type=Path, default=ROOT / 'data/dailytalk')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/oddmouth.json')
    parser.add_argument('--device', choices=['mps', 'cpu', 'cuda'], default=None)
    parser.add_argument('--fresh', action='store_true', help='Ignore an existing checkpoint (refuses to overwrite)')
    parser.add_argument('--log-every', type=int, default=25)
    parser.add_argument('--eval-every', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--cpu-share', type=float, default=None, help='Target CPU share, up to 0.30 on a Mac or CPU; up to 1.0 with --device cuda (default: 0.25)')
    parser.add_argument('--profile', action='store_true', help='Break down setup and synchronized step timings')
    args = parser.parse_args()

    stopping = False

    def request_stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    cfg = json.loads(args.config.read_text())
    stage_cfg, arch = cfg['training'][args.stage], cfg['architecture']
    device = torch.device(args.device or cfg['training']['device'])
    if device.type == 'mps' and not torch.backends.mps.is_available():
        raise RuntimeError('MPS unavailable; pass --device cpu')
    if device.type == 'cuda':
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA unavailable')
        # Cloud GPUs train with larger batches; see training.cuda in the config.
        stage_cfg = {**stage_cfg, **cfg['training'].get('cuda', {}).get(args.stage, {})}
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    run = args.run or ROOT / 'runs' / args.stage
    run.mkdir(parents=True, exist_ok=True)
    ckpt_path = run / 'last.pt'
    if args.fresh and ckpt_path.exists():
        raise FileExistsError(f'{ckpt_path} exists; choose another --run to start fresh')
    reserve = cfg['storage']['minimum_free_disk_bytes']
    share = args.cpu_share if args.cpu_share is not None else cfg['cpu_share']
    # The 0.30 cap protects the user's Mac; rented cloud GPU machines may use all cores.
    if not 0 < share <= (1.0 if device.type == 'cuda' else 0.30):
        parser.error('CPU share must be greater than zero and at most 0.30 (1.0 with --device cuda)')
    limit_threads(share)
    limiter = CpuLimiter(share)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)

    setup_started = time.monotonic()
    splits, manifest = load_acoustic(args.data)
    if args.profile:
        print(json.dumps({'profile': 'load_acoustic', 'seconds': time.monotonic() - setup_started}), flush=True)
    train, evaluation = splits['train'], splits['eval']
    if args.stage == 'acoustic':
        model = AcousticModel(arch, VOCAB_SIZE)
        model.mel_mean.copy_(torch.tensor(manifest['mel_mean']))
        model.mel_std.copy_(torch.tensor(manifest['mel_std']))
        disc = None
        optimizer = torch.optim.AdamW(model.parameters(), lr=stage_cfg['learning_rate'],
                                      weight_decay=stage_cfg['weight_decay'])
        warmup = stage_cfg['warmup_steps']
    else:
        model, disc = Vocoder(arch), Discriminators()
        betas = tuple(stage_cfg['betas'])
        optimizer = torch.optim.AdamW(model.parameters(), lr=stage_cfg['learning_rate'], betas=betas)
        d_optimizer = torch.optim.AdamW(disc.parameters(), lr=stage_cfg['learning_rate'], betas=betas)
        wave_load_started = time.monotonic()
        waves = load_waves(args.data, manifest['shards'])
        if args.profile:
            print(json.dumps({'profile': 'load_waves', 'seconds': time.monotonic() - wave_load_started}), flush=True)
        train = [x for x in train if x['id'] in waves and x['mel'].shape[-1] >= stage_cfg['segment_frames']]
        evaluation = [x for x in evaluation if x['id'] in waves]
        if len(train) < stage_cfg['batch_size']:
            raise ValueError('Not enough waveform clips for the configured vocoder batch size')
        warmup = 0
    total_steps = stage_cfg['total_steps']
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, schedule(warmup, total_steps))
    d_scheduler = (torch.optim.lr_scheduler.LambdaLR(d_optimizer, schedule(0, total_steps))
                   if disc is not None else None)

    step, epoch, cursor = 0, 0, 0
    if ckpt_path.exists():
        state = torch.load(ckpt_path, map_location='cpu', weights_only=False)
        if state['stage'] != args.stage or state['architecture'] != arch:
            raise ValueError('Checkpoint stage/architecture differs from config')
        model.load_state_dict(state['model'])
        optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler'])
        if disc is not None:
            disc.load_state_dict(state['discriminators'])
            d_optimizer.load_state_dict(state['d_optimizer'])
            d_scheduler.load_state_dict(state['d_scheduler'])
        step, epoch, cursor = state['step'], state['epoch'], state['cursor']
        torch.set_rng_state(state['torch_rng'])
        random.setstate(state['python_rng'])
        del state
        print(f'resumed {args.stage} at step {step}', flush=True)
    model.to(device).train()
    if disc is not None:
        disc.to(device).train()
    optimizer_to(optimizer, device)
    if disc is not None:
        optimizer_to(d_optimizer, device)

    def checkpoint():
        state = {'stage': args.stage, 'architecture': arch, 'symbol_version': SYMBOL_VERSION,
                 'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                 'scheduler': scheduler.state_dict(), 'step': step, 'epoch': epoch, 'cursor': cursor,
                 'torch_rng': torch.get_rng_state(), 'python_rng': random.getstate(),
                 'data': {'hf_repo': manifest['hf_repo'], 'hf_revision': manifest['hf_revision']},
                 'saved_utc': datetime.now(timezone.utc).isoformat(),
                 'initialization': 'random; no pretrained weights'}
        if disc is not None:
            state.update(discriminators=disc.state_dict(), d_optimizer=d_optimizer.state_dict(),
                         d_scheduler=d_scheduler.state_dict())
        save_checkpoint(ckpt_path, state, reserve)

    @torch.no_grad()
    def evaluate():
        model.eval()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(2026)
            if args.stage == 'acoustic':
                losses = []
                eval_batches = frame_batches(evaluation, stage_cfg['batch_frames'],
                                             stage_cfg['max_batch'], 2026)
                for indices in eval_batches:
                    batch = collate([evaluation[i] for i in indices], device)
                    losses.append(float(model.losses(*batch)[0]))
                result = {'eval_loss': float(np.mean(losses))}
                vocoder_ckpt = run.parent / 'vocoder/last.pt'  # sibling run, e.g. runs/vocoder
                if vocoder_ckpt.exists():
                    sample = evaluation[0]
                    mel, _ = model.synthesize(sample['tokens'][None].long().to(device),
                                              torch.tensor([len(sample['tokens'])], device=device),
                                              steps=cfg['training']['synthesis_flow_steps'])
                    vocoder = Vocoder(arch)
                    vocoder.load_state_dict(torch.load(vocoder_ckpt, map_location='cpu', weights_only=False)['model'])
                    write_wav(run / 'samples' / f'step-{step:07d}.wav', vocoder.eval()(mel.cpu())[0, 0])
            else:
                errors = []
                for i, sample in enumerate(evaluation[:8]):
                    mel = sample['mel'][None].float().to(device)
                    fake = model(mel)[:, 0]
                    errors.append(float(F.l1_loss(mel_spectrogram(fake), mel)))
                    if i < 2:
                        write_wav(run / 'samples' / f'step-{step:07d}-{i}.wav', fake[0])
                result = {'eval_mel_l1': float(np.mean(errors))}
        model.train()
        return result

    print(json.dumps({'stage': args.stage, 'device': str(device), 'parameters': count(model),
                      'discriminator_parameters_training_only': count(disc) if disc is not None else 0,
                      'train_clips': len(train), 'eval_clips': len(evaluation), 'start_step': step}), flush=True)
    batches = frame_batches(train, stage_cfg['batch_frames'], stage_cfg['max_batch'], args.seed + epoch) \
        if args.stage == 'acoustic' else None
    began = time.monotonic()
    last_save = began
    stop_step = step + args.steps if args.steps else total_steps
    last_log = began
    logged_from_step = step
    totals = {}
    try:
        while step < stop_step and not stopping:
            if args.minutes and time.monotonic() - began > args.minutes * 60:
                break
            timings = {}
            phase_started = time.monotonic()

            def mark(phase):
                nonlocal phase_started
                if args.profile:
                    sync(device)
                    now = time.monotonic()
                    timings[phase] = now - phase_started
                    phase_started = now

            if args.stage == 'acoustic':
                if cursor >= len(batches):
                    epoch, cursor = epoch + 1, 0
                    batches = frame_batches(train, stage_cfg['batch_frames'], stage_cfg['max_batch'], args.seed + epoch)
                items = [train[i] for i in batches[cursor]]
                cursor += 1
                batch = collate(items, device)
                mark('collate')
                loss, parts = model.losses(*batch, profile=timings if args.profile else None)
                mark('forward_including_alignment')
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                mark('backward')
                grad = torch.nn.utils.clip_grad_norm_(model.parameters(), stage_cfg['gradient_clip_norm'])
                optimizer.step()
                scheduler.step()
                mark('optimizer')
            else:
                segment = stage_cfg['segment_frames']
                mels, reals = [], []
                for item in random.sample(train, stage_cfg['batch_size']):
                    start = random.randint(0, item['mel'].shape[-1] - segment)
                    mels.append(item['mel'][:, start:start + segment].float())
                    wave = waves[item['id']][start * HOP:(start + segment) * HOP].float() / 32767
                    reals.append(wave)
                mel = torch.stack(mels).to(device)
                real = torch.stack(reals)[:, None].to(device)
                mark('collate')
                fake = model(mel)
                adversarial_on = step >= stage_cfg['adversarial_start_step']
                parts = {}
                if adversarial_on:
                    d_loss = discriminator_loss(disc(real), disc(fake.detach()))
                    d_optimizer.zero_grad(set_to_none=True)
                    d_loss.backward()
                    torch.nn.utils.clip_grad_norm_(disc.parameters(), stage_cfg['gradient_clip_norm'])
                    d_optimizer.step()
                    parts['discriminator'] = d_loss
                    d_scheduler.step()
                mel_loss = F.l1_loss(mel_spectrogram(fake[:, 0]), mel_spectrogram(real[:, 0]))
                loss = stage_cfg['mel_loss_weight'] * mel_loss
                parts['mel'] = mel_loss
                if adversarial_on:
                    for p in disc.parameters():
                        p.requires_grad_(False)
                    adversarial, matching = generator_losses(disc(real), disc(fake))
                    for p in disc.parameters():
                        p.requires_grad_(True)
                    loss = loss + adversarial + stage_cfg['feature_matching_weight'] * matching
                    parts.update(adversarial=adversarial, feature_matching=matching)
                mark('forward_and_discriminator')
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                mark('backward')
                grad = torch.nn.utils.clip_grad_norm_(model.parameters(), stage_cfg['gradient_clip_norm'])
                optimizer.step()
                scheduler.step()
                mark('optimizer')
            if not torch.isfinite(loss):
                raise FloatingPointError(f'Non-finite loss at step {step}')
            step += 1
            limiter()
            mark('cpu_limiter')
            if args.profile:
                print(json.dumps({'profile': 'step', 'step': step, 'seconds': timings}), flush=True)
            for key, value in {'loss': loss, **parts}.items():
                totals[key] = totals.get(key, 0.0) + float(value.detach())
            if step % args.log_every == 0:
                sync(device)
                updates = step - logged_from_step
                row = {'step': step, 'epoch': epoch, **{k: v / updates for k, v in totals.items()},
                       'grad_norm': float(grad), 'lr': scheduler.get_last_lr()[0],
                       'seconds_per_step': (time.monotonic() - last_log) / updates,
                       'mps_bytes': memory(device), **host_memory_mb()}
                last_log = time.monotonic()
                logged_from_step = step
                totals = {}
                with (run / 'metrics.jsonl').open('a') as log:
                    log.write(json.dumps(row) + '\n')
                print(json.dumps(row), flush=True)
            if not stopping and step % args.eval_every == 0:
                result = {'step': step, **evaluate()}
                with (run / 'metrics.jsonl').open('a') as log:
                    log.write(json.dumps(result) + '\n')
                print(json.dumps(result), flush=True)
            if time.monotonic() - last_save > cfg['training']['checkpoint_every_minutes'] * 60:
                checkpoint()
                last_save = time.monotonic()
    except KeyboardInterrupt:
        print('interrupted; saving checkpoint', flush=True)
    if stopping:
        print('Stop requested; saving at the update boundary', flush=True)
    checkpoint()
    elapsed = time.monotonic() - began
    print(json.dumps({'saved': str(ckpt_path), 'step': step, 'elapsed_minutes': elapsed / 60}), flush=True)


def optimizer_to(optimizer, device):
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


if __name__ == '__main__':
    main()
