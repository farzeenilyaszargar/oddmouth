# Oddmouth

Oddmouth is a planned single-voice text-to-speech system for warm, deep male narration and conversational speech, designed to run locally in a web browser.

The target is a complete deployed neural pipeline of approximately 50 million parameters or fewer, with offline generation after the initial download and no provider character quota.

## Current status

The user has selected **Dewayne Noel / Dry Creek Wrangler** for expressive, conversational YouTube-style delivery, with planned `[happy]` and `[angry]` controls. Recording/model-distribution rights and clean training hours remain unverified; see [the training preparation plan](DEWAYNE_TRAINING_PLAN.md). Necessary downloads are conditionally authorized in chunks of at most 1 GB; none were necessary for this planning update. No custom model has been trained yet, and ElevenLabs-level quality or emotion control has not been demonstrated.

The [Mac training system plan](MAC_TRAINING_SYSTEM.md) targets the measured M2 MacBook Air with 8 GiB memory. It specifies a pretrained baseline, a hypothetical 46.5M complete architecture, bounded data rotation, staged experiments, and browser export gates. Reproduce the planning report with `python3 scripts/plan_training.py --output reports/mac_training_preflight.json`; run the storage/planning checks with `python3 -m unittest discover -s tests -v`. These utilities do not download audio or train a model.

## Web demo

The minimal Next.js frontend lives in [`web/`](web/README.md), with the tagline **Small model. Big mouth.** Run `cd web && npm ci && npm run dev` to preview it. It includes an editable text box and a five-second prerecorded sample with play/pause, seeking, and WAV download. Custom Oddmouth synthesis is not connected yet.

## Project documents

- [Research and implementation plan](VOICE_MODEL_PLAN.md)
- [Research scope and unresolved experiments](RESEARCH_SCOPE.md)
- [Initial evaluation prompts](VOICE_EVALUATION_PROMPTS.tsv)
- [Single-speaker data source and streaming samples](DATA_SOURCE.md)
- [Planned emotion tags and training requirements](EXPRESSION_CONTROLS.md)
- [Mark Nelson narration candidate and 55-hour source inventory](MARK_NELSON_SOURCE.md)
- [Current story-and-lessons audition lead: Dewayne Noel](DEWAYNE_NOEL_SOURCE.md)

## Repository

The canonical repository is [farzeenilyaszargar/oddmouth](https://github.com/farzeenilyaszargar/oddmouth). Project updates are committed and pushed here after each completed update.
