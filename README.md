# Oddmouth

Oddmouth is a small single-voice text-to-speech system for natural, conversational male narration in videos, trained locally and designed to run offline (and eventually in the browser).

The complete deployed model stays under 15 million parameters, with no provider character quota.

## Current status

Oddmouth is a **14.56M-parameter** single-voice model: a Matcha-style flow-matching acoustic model (8.6M) and a Vocos-style vocoder (6.0M). Both are trained from random weights on one speaker on an M2 MacBook Air, using at most about 25% of the CPU. The training data is the **DailyTalk male speaker**: about 10.8 hours of transcribed conversational studio speech, streamed from Hugging Face. The code is implemented and tested; **no trained voice exists yet**, and real-data speed and quality are unmeasured. The DailyTalk licence does not clearly allow commercial use. See [MAC_TRAINING_SYSTEM.md](MAC_TRAINING_SYSTEM.md) and [DATA_SOURCE.md](DATA_SOURCE.md).

## Quick start

```bash
uv sync                                                    # needs espeak-ng: brew install espeak-ng
uv run python scripts/prepare_dailytalk.py                 # stream + prepare data (~0.9 GB, resumable)
uv run python scripts/train.py --stage vocoder --minutes 60
uv run python scripts/train.py --stage acoustic --minutes 60
uv run python scripts/speak.py "Hey everyone, welcome back." --out outputs/hello.wav
uv run python -m unittest discover -s tests
```

Training resumes automatically, saves every 10 minutes and on Ctrl-C, and writes listening samples to `runs/<stage>/samples/`.

## Web demo

The minimal Next.js frontend lives in [`web/`](web/README.md), with the tagline **Small model. Big mouth.** Run `cd web && npm ci && npm run dev` to preview it. It includes an editable text box and a five-second prerecorded sample with play/pause, seeking, and WAV download. Custom Oddmouth synthesis is not connected yet.

## Project documents

- [Research and implementation plan](VOICE_MODEL_PLAN.md)
- [Research scope and unresolved experiments](RESEARCH_SCOPE.md)
- [Initial evaluation prompts](VOICE_EVALUATION_PROMPTS.tsv)
- [Single-speaker data source and streaming samples](DATA_SOURCE.md)
- [Natural delivery scope; emotion controls removed](EXPRESSION_CONTROLS.md)
- [Mark Nelson narration candidate and 55-hour source inventory](MARK_NELSON_SOURCE.md)
- [Current story-and-lessons audition lead: Dewayne Noel](DEWAYNE_NOEL_SOURCE.md)

## Repository

The canonical repository is [farzeenilyaszargar/oddmouth](https://github.com/farzeenilyaszargar/oddmouth). Project updates are committed and pushed here after each completed update.
