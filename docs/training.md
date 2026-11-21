# Training Oddmouth

## Model

Oddmouth has two networks, trained separately and both from random weights.

```
text ─▶ espeak-ng phonemes ─▶ [ acoustic model ] ─▶ mel spectrogram ─▶ [ vocoder ] ─▶ audio
```

| Part | Design | Parameters |
|---|---|---:|
| Text encoder | 4 transformer blocks, width 192 | 1,820,928 |
| Duration predictor | 2 conv layers, predicts frames per phoneme | 222,529 |
| Flow decoder | 8 transformer blocks, width 256, conditional flow matching | 6,499,664 |
| Other projections | | 64,848 |
| **Acoustic model** | Based on [Matcha-TTS](https://arxiv.org/abs/2309.03199) | **8,607,969** |
| **Vocoder** | Based on [Vocos](https://arxiv.org/abs/2306.00814): 6 ConvNeXt blocks, width 384, predicts STFT magnitude and phase | **5,954,946** |
| **Total shipped** | | **14,562,915** |
| Discriminators | Training only, never shipped: 5 period + 3 spectrogram discriminators ([HiFi-GAN](https://arxiv.org/abs/2010.05646)-style) | 2,846,344 |

Design choices that keep training fast on a laptop:

- **Alignment is learned during training.** Monotonic alignment search matches phonemes to frames, so no external forced aligner is needed.
- **Batches are sized by audio length.** On an 8 GB Mac the acoustic default targets 1,024 padded mel frames and at most four clips. The vocoder uses four segments of 8,192 samples.
- **The vocoder predicts a spectrogram and inverts it** with a fixed transposed convolution (an exact inverse STFT). This avoids slow upsampling stacks and complex-number operations, so it runs on Apple's GPU (MPS) and can be exported to ONNX.

## Audio format

22,050 Hz mono, 80 mel bins (0–8 kHz), FFT 1024, hop 256, natural-log mel. A clip of `L` samples gives exactly `L / 256` frames. The acoustic model normalizes mels with training-set statistics stored inside the checkpoint.

## Running

```bash
uv run python scripts/prepare_dailytalk.py                   # once; resumable
uv run python scripts/train.py --stage vocoder  --minutes 60
uv run python scripts/train.py --stage acoustic --minutes 60
```

- **Resumable:** each run continues from `runs/<stage>/last.pt`, saves every 10 minutes and on Ctrl-C. Train in as many sessions as you like.
- **Listen as it learns:** the vocoder writes held-out reconstructions to `runs/vocoder/samples/` every 1,000 steps. Once a vocoder checkpoint exists, the acoustic stage writes text-to-speech samples to `runs/acoustic/samples/`.
- **Metrics:** `runs/<stage>/metrics.jsonl` logs losses, seconds per step and GPU memory.
- **CPU cap:** training limits compute threads and throttles toward an average `cpu_share` of total CPU. The default is 0.25 and overrides can go up to 0.30.
- **Options:** `--steps N` stops after N updates, `--device cpu` runs without MPS, `--run DIR` selects a run directory, and `--profile --log-every 1` prints stage timings.

Configured upper bounds are 150k acoustic and 300k vocoder steps. Stop earlier when the samples sound good.

To run both stages in consecutive parts, use `uv run --extra browser python scripts/train_in_parts.py`. The runner finishes the vocoder reconstruction warmup first, then advances both stages toward their configured limits. It saves after each part and exports periodic browser previews. Use one runner at a time. Ctrl-C requests a save at the next update boundary. Progress is recorded in `runs/continuous-status.json`.

## Generating speech

```bash
uv run python scripts/speak.py "Hey everyone, welcome back." --out outputs/hello.wav
uv run python scripts/speak.py --file script.txt --out outputs/video.wav --speed 1.05
```

Text is split into sentences and joined with short pauses, so any length works. `--steps` (flow steps, default 8) trades speed for quality; `--temperature` controls variation.

## Measured so far

| Check | Result |
|---|---|
| Unit tests | 13 passing |
| Acoustic smoke run, synthetic data, M2 Air MPS | ~0.8 s/step, ~150 MB GPU memory |
| Vocoder smoke run, synthetic data, batch 16 × 8,192 samples | ~1.2 s/step (before the GAN starts) |
| DailyTalk acoustic, M2 Air MPS | 6 updates, 1.37 s/update median, up to 215 MB allocated MPS memory at logging |
| DailyTalk vocoder, M2 Air MPS | 6 reconstruction updates, 0.41 s/update median, up to 130 MB allocated MPS memory at logging |

Both real-data runs used the default 25% CPU share and saved local checkpoints. The timing includes the first update. Alignment took 7–52 ms per acoustic update, and the CPU limiter took 1–33 ms. The short runs only establish that updates complete. Sustained throughput, adversarial training, convergence and voice quality still need measurement.

## Evaluation

[`eval_prompts.tsv`](eval_prompts.tsv) lists fixed sentences for listening tests. Check intelligibility on unseen text, timing, pronunciation of numbers and names, and stability on long passages.
