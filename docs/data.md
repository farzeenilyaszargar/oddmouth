# Training data

## DailyTalk, male speaker

[DailyTalk](https://github.com/keonlee9420/DailyTalk) ([paper](https://arxiv.org/abs/2207.01063)) is studio-recorded conversational English made for text-to-speech, with transcripts. Oddmouth uses only its male speaker: 11,867 clips and 38,902 seconds (about 10.8 hours) in the paper's table.

`scripts/prepare_dailytalk.py` reads the Hugging Face mirror [innovationm-ai/dailytalk-male](https://huggingface.co/datasets/innovationm-ai/dailytalk-male), pinned to a fixed revision in [`configs/oddmouth.json`](../configs/oddmouth.json). For each clip it:

1. streams one parquet row group (~90 MB) at a time into memory, never saving raw audio;
2. trims silence and resamples 24 kHz to 22.05 kHz;
3. converts text to phonemes with espeak-ng;
4. stores an fp16 mel and phoneme tokens, plus int16 audio for 20% of clips (vocoder training) and the last 150 clips (held-out evaluation).

Output goes to `data/dailytalk/` (about 0.9 GB, capped at 1 GB). `manifest.json` records hours, clip counts, normalization statistics, unknown phoneme symbols and a rough median pitch.

## Licence

- **DailyTalk:** CC-BY-SA 4.0. The authors describe it as "freely available for academic use".
- **Dialogue text:** comes from [DailyDialog](http://yanran.li/dailydialog), which is CC-BY-NC-SA 4.0.
- **Mirror label:** the mirror's "apache-2.0" tag is not authoritative; the original licence governs.

**Commercial use of voices trained on this data is not cleared.** Check with the dataset authors before using the output in monetized content. Oddmouth's code licence is separate from any trained voice.

## Why this dataset

Requirements: one male speaker, natural conversational delivery, clean audio, existing transcripts, easy to download again, and no audiobook reading.

| Dataset | Fit | Why not chosen |
|---|---|---|
| **DailyTalk (male)** | ~10.8 h conversational studio speech, transcribed | Chosen |
| [Expresso](https://speechbot.github.io/expresso) | Expressive, includes improvised dialogue; ~10 h per speaker | CC-BY-NC 4.0 (non-commercial) |
| [RyanSpeech](https://arxiv.org/abs/2106.08468) | >10 h professional male voice, conversational text | CC-BY-NC-ND (non-commercial, no derivatives) |
| Hi-Fi TTS, LibriTTS-R, LJSpeech | Large and permissive | Audiobook reading style, or female voice |
| Raw podcasts or YouTube channels | Lots of audio | Need speaker separation, cleaning and transcription; rights unclear |

## Using another speaker

Any single-speaker dataset with transcripts works. Write a prepare script that produces the same shard format (`acoustic-N.pt`, `waves-N.pt`, `manifest.json`); the trainer doesn't depend on DailyTalk. Train on one speaker only: Oddmouth has no speaker embedding.
