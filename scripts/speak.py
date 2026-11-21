"""Generate speech with trained Oddmouth checkpoints, fully offline.

    uv run python scripts/speak.py "Hey everyone, welcome back." --out outputs/hello.wav
    uv run python scripts/speak.py --file script.txt --out outputs/video.wav

Long text is split into sentences, synthesized one at a time and joined with
short pauses, so any length works.
"""
import argparse
from pathlib import Path
import re
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oddmouth.audio import SR  # noqa: E402
from oddmouth.model import AcousticModel, Vocoder  # noqa: E402
from oddmouth.text import SYMBOL_VERSION, VOCAB_SIZE, encode, phonemize  # noqa: E402


def sentences(text):
    parts = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def load(path, build):
    state = torch.load(path, map_location='cpu', weights_only=False)
    if state.get('symbol_version') != SYMBOL_VERSION:
        raise ValueError(f'{path} uses a different symbol table')
    model = build(state['architecture'])
    model.load_state_dict(state['model'])
    return model.eval(), state['step']


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('text', nargs='?')
    parser.add_argument('--file', type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'outputs/speech.wav')
    parser.add_argument('--acoustic', type=Path, default=ROOT / 'runs/acoustic/last.pt')
    parser.add_argument('--vocoder', type=Path, default=ROOT / 'runs/vocoder/last.pt')
    parser.add_argument('--steps', type=int, default=8, help='Flow steps: more is slower, often cleaner')
    parser.add_argument('--temperature', type=float, default=0.667)
    parser.add_argument('--speed', type=float, default=1.0, help='>1 is faster speech')
    parser.add_argument('--pause', type=float, default=0.25, help='Seconds between sentences')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    text = args.file.read_text() if args.file else args.text
    if not text:
        parser.error('give text or --file')
    torch.manual_seed(args.seed)
    acoustic, a_step = load(args.acoustic, lambda a: AcousticModel(a, VOCAB_SIZE))
    vocoder, v_step = load(args.vocoder, Vocoder)
    chunks = sentences(text)
    pieces, silence = [], np.zeros(int(args.pause * SR), dtype=np.float32)
    with torch.no_grad():
        for sentence, ipa in zip(chunks, phonemize(chunks)):
            tokens = encode(ipa)[None]
            mel, _ = acoustic.synthesize(tokens, torch.tensor([tokens.shape[1]]), steps=args.steps,
                                         temperature=args.temperature, length_scale=1 / args.speed)
            pieces += [vocoder(mel)[0, 0].clamp(-1, 1).numpy(), silence]
    audio = np.concatenate(pieces[:-1])
    from scipy.io import wavfile
    args.out.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(args.out, SR, (audio * 32767).astype(np.int16))
    print(f'wrote {args.out} ({len(audio) / SR:.1f}s; acoustic step {a_step}, vocoder step {v_step})')


if __name__ == '__main__':
    main()
