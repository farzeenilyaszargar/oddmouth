# Oddmouth

Oddmouth is a planned single-voice text-to-speech system for warm, deep male narration and conversational speech, designed to run locally in a web browser.

The target is a complete deployed neural pipeline of approximately 50 million parameters or fewer, with offline generation after the initial download and no provider character quota.

## Current status

The current plan is to train **one voice entirely from scratch**, including the acoustic model and vocoder, using only the selected speaker's recordings. There are **no explicit emotion controls** and no pretrained TTS/vocoder initialization or teacher distillation. The user selected Dewayne Noel / Dry Creek Wrangler for naturally engaging narration. Recording rights and clean usable hours remain unverified.

The [Mac training system plan](MAC_TRAINING_SYSTEM.md) targets the M2 MacBook Air with 8 GiB memory. It specifies a hypothetical 46.41M complete architecture, separate acoustic and waveform training phases, a 1 GB combined data cache, resumable runs, and browser export gates. No custom model has been trained and no voice audio was downloaded for planning.

Reproduce the planning report with `python3 scripts/plan_training.py --output reports/mac_training_preflight.json`; run scope/storage checks with `python3 -m unittest discover -s tests -v`. These utilities do not download audio or train speech. Necessary future downloads remain capped at 1,000,000,000 bytes per chunk.

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
