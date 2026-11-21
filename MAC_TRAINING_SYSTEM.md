# Oddmouth: a 15M voice model trained on the Mac

Updated 21 November 2026. This replaces the earlier 46M design and the Dewayne Noel data plan. The code is implemented and passes unit tests and synthetic MPS smoke runs. **No trained voice exists yet, and speech quality has not been measured.**

## Fixed scope

- One male, conversational voice for narration and developer or social-media videos.
- Every deployed network (acoustic model and vocoder) starts from random weights. No pretrained TTS or vocoder weights, fine-tuning, distillation, or other-speaker audio.
- No emotion controls.
- At most 15M deployed parameters. Discriminators are used only during training and are never shipped.
- Downloads come in chunks of at most 1 GB; prepared features stay within a 1 GB managed cache.
- Jobs use at most about 25% of total CPU (`cpu_share` in [configs/mac_training.json](configs/mac_training.json), enforced by [oddmouth/throttle.py](oddmouth/throttle.py)).

## Architecture (14.56M deployed parameters, counted from the real modules)

| Part | Design | Parameters |
|---|---|---:|
| Text frontend | espeak-ng IPA with a fixed 182-symbol table and blanks between symbols | 0 |
| Text encoder + embedding | 4 blocks, width 192 (self-attention + depthwise conv + MLP) | 1,820,928 |
| Duration predictor | 2 conv layers; predicts log frames per token | 222,529 |
| Flow decoder | 8 blocks, width 256; conditional flow matching on normalized mels, conditioned on the aligned text prior | 6,499,664 |
| **Acoustic total** | | **8,607,969** |
| Vocoder | Vocos-style: 6 ConvNeXt blocks, width 384, predicts STFT magnitude and phase; the inverse STFT is a fixed transposed convolution | **5,954,946** |
| Discriminators (training only) | 5 period discriminators + 3 spectrogram-resolution discriminators | 2,846,344 |

Why this trains faster than the old plan:

- **Smaller.** 14.6M parameters instead of 46M.
- **Real batches.** Batches are sized by a frame budget of up to 6,000 mel frames, instead of one clip at a time with 16-step accumulation.
- **Alignment learned in training.** Monotonic alignment search runs on the CPU, vectorized over each batch, so no external aligner is needed.
- **A faster vocoder.** It predicts a spectrogram and inverts it, instead of upsampling sample by sample like HiFi-GAN. This usually converges much faster. Because it uses no complex-number operations, it runs on MPS and should export to ONNX for the browser. ONNX export has not been tested yet.

References: [Matcha-TTS](https://arxiv.org/abs/2309.03199) (flow matching + monotonic alignment), [Vocos](https://arxiv.org/abs/2306.00814) (Fourier-domain vocoder), [HiFi-GAN](https://arxiv.org/abs/2010.05646) (discriminators and losses). The code is a fresh implementation; no checkpoints are loaded.

## Audio convention

22,050 Hz mono, 80 mel bins at 0–8 kHz, FFT 1024, hop 256, natural-log magnitude mel with a 1e-5 floor. A clip of L samples gives exactly L/256 mel frames, which keeps vocoder segments aligned. The acoustic model works in mel space normalized by training-set statistics (stored in the model). The vocoder takes raw log mel.

## Data: DailyTalk male speaker

See [DATA_SOURCE.md](DATA_SOURCE.md) for the reasoning and alternatives. In short:

- [DailyTalk](https://github.com/keonlee9420/DailyTalk) is studio-recorded conversational English made for TTS, with transcripts. The male speaker has 11,867 clips and 38,902 s (about 10.8 h) in the paper's table.
- It is streamed from the Hugging Face mirror [innovationm-ai/dailytalk-male](https://huggingface.co/datasets/innovationm-ai/dailytalk-male), pinned at revision `418c0830…`: four parquet files of about 440 MB, read one row group (~90 MB) at a time into memory.
- Preparation trims silence, resamples 24 kHz to 22.05 kHz, phonemizes, and stores fp16 mels and tokens for every clip. It keeps int16 waveforms for 20% of clips (vocoder training) and for the last 150 clips (held-out evaluation). Expected size is about 0.9 GB.
- **Licence:** CC-BY-SA 4.0, described by the authors as "for academic use"; the dialogue text comes from DailyDialog (CC-BY-NC-SA 4.0). Treat commercial or monetized use as **not cleared**. The mirror's "apache-2.0" label is not authoritative.
- 10.8 h is below the earlier 50-hour preference, but it is a normal size for a single-speaker model of this size.

## How to run

```bash
uv sync
uv run python scripts/prepare_dailytalk.py           # once; resumable
uv run python scripts/train.py --stage vocoder --minutes 60
uv run python scripts/train.py --stage acoustic --minutes 60
uv run python scripts/speak.py "Hey everyone, welcome back." --out outputs/hello.wav
```

- Run one stage per process. Each run resumes from `runs/<stage>/last.pt`, saves every 10 minutes, and saves on Ctrl-C, so training can be spread across many laptop sessions.
- The vocoder writes reconstructions of held-out clips to `runs/vocoder/samples/` every 1,000 steps. Once a vocoder checkpoint exists, the acoustic stage also writes text-to-speech samples to `runs/acoustic/samples/`.
- `metrics.jsonl` in each run logs losses, seconds per step and MPS memory.
- Targets in config: 150k acoustic steps and 300k vocoder steps. These are upper bounds from published recipes; stop earlier when the samples sound good.

## Measured so far

| Check | Result |
|---|---|
| Unit tests (inverse STFT round trip, alignment validity, shapes, parameter limit) | 14 passing |
| Synthetic-data MPS smoke run, acoustic (batches up to 32 random clips) | ~0.8 s/step, ~150 MB MPS memory, resume works |
| Synthetic-data MPS smoke run, vocoder (batch 16 × 8,192 samples, before the GAN starts) | ~1.2 s/step |
| CPU while throttled | 30–48% of one core in `ps` (~5% of the 8-core machine) |
| Real-data throughput, convergence, voice quality | **Not measured yet** |

Rough time arithmetic, not a promise: at about 1 s/step, 50k steps is about 14 hours of training per stage. Real numbers come from the first real-data runs.

## Next steps

1. Finish data preparation and check the manifest: hours, median F0 (to confirm a male voice), and unknown phoneme symbols.
2. Listen to a few prepared clips to confirm the voice is wanted.
3. Benchmark both stages on real data; tune batch frames and the CPU share against speed.
4. Train the vocoder first, then the acoustic model, listening to samples along the way.
5. Export to ONNX and test in the browser.
