"""Prepare the DailyTalk male speaker for Oddmouth training. One command, resumable.

    uv run python scripts/prepare_dailytalk.py

Streams the pinned Hugging Face parquet files one row group (~90 MB) at a time
into memory; raw audio is never written to disk. Each source file becomes one
feature shard (mel + tokens for every clip, waveforms for a fixed fraction of
clips for vocoder training). All writes go through the bounded cache writer.
Re-running skips finished shards; delete data/dailytalk to start over.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oddmouth.cache import cache_bytes, write_bounded  # noqa: E402
from oddmouth.audio import HOP, SR, decode_audio, mel_spectrogram, median_f0, trim_silence  # noqa: E402
from oddmouth.text import SYMBOL_VERSION, clean, encode, phonemize  # noqa: E402
from oddmouth.throttle import CpuLimiter, limit_threads  # noqa: E402

MIN_SECONDS, MAX_SECONDS = 0.6, 12.0


def keep_wave(clip_id, fraction):
    digest = hashlib.sha256(clip_id.encode()).digest()
    return int.from_bytes(digest[:4], 'big') / 2 ** 32 < fraction


def save(obj, path, root, limits):
    buffer = io.BytesIO()
    torch.save(obj, buffer)
    write_bounded([buffer.getvalue()], path, root, file_limit=limits['file'],
                  cache_limit=limits['cache'], reserve_bytes=limits['reserve'])


def prepare_file(fs, remote, shard_index, is_last, cfg, root, limits, unknown, limiter):
    import pyarrow.parquet as pq
    source = cfg['data_source']
    fraction = cfg['storage']['vocoder_wave_fraction']
    acoustic = {'ids': [], 'texts': [], 'phonemes': [], 'tokens': [], 'mels': [], 'split': []}
    waves = {'ids': [], 'waves': []}
    stats = {'sum': torch.zeros(80, dtype=torch.float64), 'sumsq': torch.zeros(80, dtype=torch.float64),
             'frames': 0, 'seconds': 0.0, 'skipped': 0}
    f0 = []
    handle = fs.open(remote, block_size=16_000_000)
    parquet = pq.ParquetFile(handle)
    total_rows = parquet.metadata.num_rows
    row = 0
    for group in range(parquet.metadata.num_row_groups):
        table = parquet.read_row_group(group, columns=['text', 'audio'])
        rows = table.to_pylist()
        del table
        texts = [clean(r['text']) for r in rows]
        ipa = phonemize(texts)
        for r, text, phones in zip(rows, texts, ipa):
            limiter()
            clip_id = f'{shard_index}-{row:05d}'
            row += 1
            audio = trim_silence(decode_audio(r['audio']['bytes']))
            audio = audio[:len(audio) // HOP * HOP]
            seconds = len(audio) / SR
            tokens = encode(phones, unknown)
            frames = len(audio) // HOP
            if not text or not MIN_SECONDS <= seconds <= MAX_SECONDS or frames < len(tokens):
                stats['skipped'] += 1
                continue
            mel = mel_spectrogram(torch.from_numpy(audio))[0]
            split = 'eval' if is_last and row > total_rows - source['eval_clips'] else 'train'
            acoustic['ids'].append(clip_id)
            acoustic['texts'].append(text)
            acoustic['phonemes'].append(phones)
            acoustic['tokens'].append(tokens.to(torch.int16))
            acoustic['mels'].append(mel.to(torch.float16))
            acoustic['split'].append(split)
            if split == 'train':
                stats['sum'] += mel.double().sum(1)
                stats['sumsq'] += mel.double().square().sum(1)
                stats['frames'] += frames
            stats['seconds'] += seconds
            if split == 'eval' or keep_wave(clip_id, fraction):
                waves['ids'].append(clip_id)
                waves['waves'].append(torch.from_numpy((audio * 32767).astype(np.int16)))
            if len(f0) < 60 and row % 7 == 0:
                value = median_f0(audio)
                if value:
                    f0.append(value)
        print(json.dumps({'file': remote.rsplit('/', 1)[-1], 'row_group': group + 1,
                          'of': parquet.metadata.num_row_groups, 'clips': len(acoustic['ids'])}), flush=True)
        del rows
    handle.close()
    acoustic['stats'] = stats
    acoustic['median_f0_samples'] = f0
    save(acoustic, root / f'acoustic-{shard_index}.pt', root, limits)
    save(waves, root / f'waves-{shard_index}.pt', root, limits)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, default=ROOT / 'data/dailytalk')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/oddmouth.json')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    limit_threads(cfg['cpu_share'])
    limiter = CpuLimiter(cfg['cpu_share'])
    source, storage = cfg['data_source'], cfg['storage']
    limits = {'file': storage['max_download_chunk_bytes'], 'cache': storage['managed_data_cache_bytes'],
              'reserve': storage['minimum_free_disk_bytes']}
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import HfFileSystem
    fs = HfFileSystem()
    unknown = {}
    began = time.monotonic()
    for index, name in enumerate(source['files']):
        if (root / f'acoustic-{index}.pt').exists():
            print(f'shard {index} already prepared', flush=True)
            continue
        remote = f"datasets/{source['hf_repo']}@{source['hf_revision']}/{name}"
        prepare_file(fs, remote, index, index == len(source['files']) - 1, cfg, root, limits, unknown, limiter)

    total = {'sum': torch.zeros(80, dtype=torch.float64), 'sumsq': torch.zeros(80, dtype=torch.float64), 'frames': 0}
    counts = {'train': 0, 'eval': 0}
    seconds, skipped, wave_clips, f0 = 0.0, 0, 0, []
    for index in range(len(source['files'])):
        shard = torch.load(root / f'acoustic-{index}.pt', weights_only=True)
        for key in ('sum', 'sumsq', 'frames'):
            total[key] = total[key] + shard['stats'][key]
        for split in shard['split']:
            counts[split] += 1
        seconds += shard['stats']['seconds']
        skipped += shard['stats']['skipped']
        f0 += shard['median_f0_samples']
        wave_clips += len(torch.load(root / f'waves-{index}.pt', weights_only=True)['ids'])
    mean = total['sum'] / total['frames']
    std = (total['sumsq'] / total['frames'] - mean.square()).clamp_min(1e-6).sqrt()
    manifest = {
        'dataset': source['name'], 'hf_repo': source['hf_repo'], 'hf_revision': source['hf_revision'],
        'files': source['files'], 'original_licence': source['original_license'],
        'shards': len(source['files']), 'train_clips': counts['train'], 'eval_clips': counts['eval'],
        'skipped_clips': skipped, 'clips_with_waveforms': wave_clips,
        'hours_after_trimming': seconds / 3600,
        'median_f0_hz': float(np.median(f0)) if f0 else None,
        'f0_note': 'Rough autocorrelation diagnostic; typical adult male speech is ~85-155 Hz',
        'unknown_symbols': unknown, 'symbol_version': SYMBOL_VERSION,
        'mel_mean': mean.float().tolist(), 'mel_std': std.float().tolist(),
        'sample_rate': SR, 'hop_length': HOP, 'cache_bytes': cache_bytes(root),
        'prepare_seconds_this_run': time.monotonic() - began,
    }
    (root / 'manifest.json').unlink(missing_ok=True)
    write_bounded([json.dumps(manifest, indent=2).encode()], root / 'manifest.json', root,
                  file_limit=limits['file'], cache_limit=limits['cache'], reserve_bytes=limits['reserve'])
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('mel_mean', 'mel_std')}, indent=2))


if __name__ == '__main__':
    main()
