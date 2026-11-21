# Oddmouth

Oddmouth is a planned single-voice text-to-speech system for warm, deep male narration and conversational speech, designed to run locally in a web browser.

The target is a complete deployed neural pipeline of approximately 50 million parameters or fewer, with offline generation after the initial download and no provider character quota.

## Current status

Research and planning are complete. The first data candidate is **Hi-Fi TTS speaker 9017, John Van Stan**, with **58 hours of clean narration reported by its publisher**. See [the source details and streaming samples](DATA_SOURCE.md). The user has requested source identification only; no audio dataset has been downloaded. No custom model has been trained yet, and ElevenLabs-level quality has not been demonstrated.

## Web demo

The minimal Next.js frontend lives in [`web/`](web/README.md), with the tagline **Small model. Big mouth.** Run `cd web && npm ci && npm run dev` to preview it. It includes an editable text box and a five-second prerecorded sample with play/pause, seeking, and WAV download. Custom Oddmouth synthesis is not connected yet.

## Project documents

- [Research and implementation plan](VOICE_MODEL_PLAN.md)
- [Research scope and unresolved experiments](RESEARCH_SCOPE.md)
- [Initial evaluation prompts](VOICE_EVALUATION_PROMPTS.tsv)
- [Single-speaker data source and streaming samples](DATA_SOURCE.md)

## Repository

The canonical repository is [farzeenilyaszargar/oddmouth](https://github.com/farzeenilyaszargar/oddmouth). Project updates are committed and pushed here after each completed update.
