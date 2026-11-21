"""Export a saved training checkpoint's listening examples for local review."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oddmouth.data import load_acoustic, load_waves
from oddmouth.model import AcousticModel, Vocoder
from oddmouth.text import VOCAB_SIZE
from oddmouth.throttle import limit_threads
from scripts.speak import load
from scripts.train import write_wav


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/dailytalk')
    parser.add_argument('--stage', choices=['vocoder', 'acoustic'], required=True)
    parser.add_argument('--vocoder', type=Path, default=ROOT / 'runs/vocoder/last.pt')
    parser.add_argument('--pair-id', action='store_true',
                        help='Include the vocoder step in the ID for an acoustic review')
    args = parser.parse_args()
    config = json.loads((ROOT / 'configs/oddmouth.json').read_text())
    limit_threads(config['cpu_share'])
    torch.manual_seed(2026)

    vocoder_path = args.run / 'last.pt' if args.stage == 'vocoder' else args.vocoder
    vocoder, vocoder_step = load(vocoder_path, Vocoder)
    acoustic, step = None, vocoder_step
    if args.stage == 'acoustic':
        acoustic, step = load(args.run / 'last.pt', lambda arch: AcousticModel(arch, VOCAB_SIZE))
    splits, data = load_acoustic(args.data)
    waves = load_waves(args.data, data['shards'])
    held_out = [clip for clip in splits['eval'] if clip['id'] in waves]
    if len(held_out) < 3:
        raise ValueError('The review needs three held-out clips with reference audio')

    run_name = args.run.resolve().name
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', run_name):
        raise ValueError('Run name must use letters, digits, dashes or underscores')
    key = f'{args.stage}-{run_name}-{step:07d}'
    if args.pair_id and args.stage == 'acoustic':
        key += f'-v{vocoder_step:07d}'
    output = ROOT / 'outputs/training-review'
    output.mkdir(parents=True, exist_ok=True)
    index_path = output / 'index.json'
    reviews = json.loads(index_path.read_text()) if index_path.exists() else []
    if any(review['id'] == key for review in reviews):
        raise ValueError(f'Review already exists for {key}')
    clips = []
    examples = [held_out[i] for i in (0, len(held_out) // 2, len(held_out) - 1)]
    with tempfile.TemporaryDirectory(dir=output) as tmp:
        folder = Path(tmp)
        for number, clip in enumerate(examples, 1):
            original = waves[clip['id']].float() / 32767
            if acoustic is None:
                mel = clip['mel'][None].float()
            else:
                tokens = clip['tokens'][None].long()
                mel, _ = acoustic.synthesize(tokens, torch.tensor([tokens.shape[-1]]),
                                              steps=config['training']['synthesis_flow_steps'])
            write_wav(folder / f'{number}-reference.wav', original)
            write_wav(folder / f'{number}-output.wav', vocoder(mel)[0, 0])
            clips.append({'text': clip['text'], 'reference': f'{number}-reference.wav',
                          'output': f'{number}-output.wav'})
        destination = output / key
        destination.mkdir()
        for wav in folder.glob('*.wav'):
            os.replace(wav, destination / wav.name)
        review = {'id': key, 'stage': args.stage, 'step': step, 'vocoderStep': vocoder_step,
                  'dataset': data['dataset'], 'clips': clips}
        index_tmp = folder / 'index.json'
        index_tmp.write_text(json.dumps([review, *reviews], indent=2) + '\n')
        os.replace(index_tmp, index_path)
    print(json.dumps({'review_id': key, 'clips': len(clips)}))


if __name__ == '__main__':
    main()
