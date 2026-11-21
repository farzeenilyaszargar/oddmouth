"""Load prepared feature shards and build length-bucketed batches."""
import json
from pathlib import Path
import random

import torch


def load_manifest(root):
    return json.loads((Path(root) / 'manifest.json').read_text())


def load_acoustic(root):
    """-> {'train': [...], 'eval': [...]} of dicts with id, text, tokens, mel."""
    manifest = load_manifest(root)
    splits = {'train': [], 'eval': []}
    for index in range(manifest['shards']):
        shard = torch.load(Path(root) / f'acoustic-{index}.pt', weights_only=True)
        for i, split in enumerate(shard['split']):
            splits[split].append({'id': shard['ids'][i], 'text': shard['texts'][i],
                                  'tokens': shard['tokens'][i], 'mel': shard['mels'][i]})
    return splits, manifest


def load_waves(root, shards):
    waves = {}
    for index in range(shards):
        shard = torch.load(Path(root) / f'waves-{index}.pt', weights_only=True)
        waves.update(zip(shard['ids'], shard['waves']))
    return waves


def frame_batches(items, batch_frames, max_batch, seed):
    """Group similar-length clips so batch_size * longest_clip <= batch_frames."""
    rng = random.Random(seed)
    order = sorted(range(len(items)), key=lambda i: items[i]['mel'].shape[-1] + rng.random())
    batches, current, longest = [], [], 0
    for i in order:
        frames = items[i]['mel'].shape[-1]
        if current and (max(longest, frames) * (len(current) + 1) > batch_frames or len(current) == max_batch):
            batches.append(current)
            current, longest = [], 0
        current.append(i)
        longest = max(longest, frames)
    if current:
        batches.append(current)
    rng.shuffle(batches)
    return batches


def collate(items, device):
    token_lengths = torch.tensor([len(x['tokens']) for x in items])
    frame_lengths = torch.tensor([x['mel'].shape[-1] for x in items])
    tokens = torch.zeros(len(items), int(token_lengths.max()), dtype=torch.long)
    mels = torch.zeros(len(items), 80, int(frame_lengths.max()))
    for i, x in enumerate(items):
        tokens[i, :len(x['tokens'])] = x['tokens'].long()
        mels[i, :, :x['mel'].shape[-1]] = x['mel'].float()
    return tokens.to(device), token_lengths.to(device), mels.to(device), frame_lengths.to(device)
