# Oddmouth

**Small model. Big mouth.**

Oddmouth is a small text-to-speech model you train yourself, on a laptop, from scratch. It learns one natural, conversational male voice and generates unlimited speech offline, with no API, no character quotas and no pretrained weights.

- **14.6M parameters** in total (acoustic model and vocoder)
- **Trains on an Apple Silicon Mac** (tested on an 8 GB M2 MacBook Air) using about 25% of the CPU
- **Random initialization only:** no pretrained TTS, vocoder or teacher models
- **One command per step:** prepare data, train, speak

> **Status:** early. The full pipeline is implemented and tested, but no trained voice has been released yet, and voice quality has not been measured.

## Quick start

Requirements: macOS on Apple Silicon (Linux and CPU also work, more slowly), [uv](https://docs.astral.sh/uv/), and espeak-ng.

```bash
brew install espeak-ng
git clone https://github.com/farzeenilyaszargar/oddmouth.git && cd oddmouth
uv sync

uv run python scripts/prepare_dailytalk.py                    # download + prepare ~10 h of speech
uv run python scripts/train.py --stage vocoder  --minutes 60  # resumable; run as often as you like
uv run python scripts/train.py --stage acoustic --minutes 60
uv run python scripts/speak.py "Hey everyone, welcome back." --out outputs/hello.wav
```

Training resumes automatically, saves on Ctrl-C, and writes listening samples to `runs/<stage>/samples/`. To train faster on a free cloud GPU, see [kaggle/](kaggle/README.md).

## How it works

```
text ─▶ phonemes ─▶ acoustic model (8.6M) ─▶ mel spectrogram ─▶ vocoder (6.0M) ─▶ audio
```

- **Acoustic model:** a Matcha-TTS-style transformer with conditional flow matching. It learns phoneme timing itself during training.
- **Vocoder:** a Vocos-style network that predicts a spectrogram and inverts it exactly. It's fast to train and exportable to ONNX.

Details: [docs/training.md](docs/training.md).

## Data

The default voice is the male speaker from **DailyTalk**: about 10.8 hours of clean, transcribed, conversational studio speech. It is streamed from Hugging Face; no raw audio is stored. **Its licence does not clearly allow commercial use** (see [docs/data.md](docs/data.md)). You can swap in any single-speaker dataset that has transcripts.

## Project layout

```
oddmouth/      model, audio features, text frontend, data loading, CPU limiter
scripts/       prepare_dailytalk.py · train.py · train_cloud.py · speak.py
configs/       oddmouth.json: architecture, training, data source, limits
tests/         unit tests: python -m unittest discover -s tests
docs/          training guide, data notes, evaluation prompts
kaggle/        notebook for training on Kaggle's free GPUs
web/           Next.js demo page (prerecorded sample; not yet wired to the model)
```

## Roadmap

- [x] 15M model, data pipeline, resumable trainer, offline synthesis
- [ ] First trained voice and real-data training benchmarks
- [ ] ONNX export and in-browser generation in `web/`
- [ ] Published checkpoints, once the training-data licence allows

## Contributing

Issues and pull requests are welcome. Run `uv run python -m unittest discover -s tests` before submitting.
