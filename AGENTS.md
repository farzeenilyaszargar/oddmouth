# Oddmouth: instructions for coding agents

- Repository: https://github.com/farzeenilyaszargar/oddmouth. Commit and push after every completed update; report a push failure explicitly.
- Keep claims honest: separate research from measured results. Never claim voice quality, speed or a trained model without evidence.
- Never commit audio, prepared features, checkpoints, model weights or secrets (`data/`, `runs/`, `weights/`, `outputs/` are ignored).
- Downloads: only when needed, at most 1,000,000,000 bytes per chunk. Stream sources and keep prepared data within the 1 GB managed cache (`oddmouth/cache.py`).
- CPU: keep jobs at or below ~20–30% of total CPU (`cpu_share` in `configs/oddmouth.json`, enforced by `oddmouth/throttle.py`). Target machine: M2 MacBook Air, 8 GB; avoid heavy jobs under memory pressure.
- Model scope: at most 15M deployed parameters. Every deployed network, including the vocoder, is trained from random weights on one speaker. No pretrained TTS/vocoder weights, fine-tuning, distillation or other-speaker data. Pretrained speech recognition is allowed only for offline data preparation.
- No emotion controls, tags or labels; learn natural delivery from the recordings.
- Voice: one natural, conversational male voice for narration and developer or social-media videos. The user rejected audiobook-style reading (Hi-Fi TTS / John Van Stan, Mark Nelson). Recording the user's own voice or hiring a voice actor is ruled out.
- Data: the default is the DailyTalk male speaker (docs/data.md); its commercial use is not cleared. On 2026-11-21 the user suggested using Dewayne Noel / Dry Creek Wrangler podcast audio as the dataset instead. That source has no verified training or voice licence and needs transcription and cleaning; do not publish weights trained on it or infer public-domain status.
- Keep the public README and docs short and practical for open-source readers; put no personal or historical research notes there.

## Status (2026-11-21)

Work is **paused at the user's request**. Do not start data downloads, training or benchmarks until the user says to continue.

Done and pushed:
- 14.56M model in `oddmouth/model.py`: 8.61M Matcha-style acoustic model and 5.95M Vocos-style vocoder. Discriminators (2.85M) are used in training only.
- `scripts/prepare_dailytalk.py`, `scripts/train.py` (resumable, Ctrl-C safe, CPU-capped) and `scripts/speak.py`.
- 13 unit tests pass (`uv run python -m unittest discover -s tests`).
- Synthetic-data MPS smoke runs: acoustic ~0.8 s/step, vocoder ~1.2 s/step.

Local only (git-ignored; rebuild with `scripts/prepare_dailytalk.py`, ~16 min):
- `data/dailytalk/`: 9.2 h after trimming, 11,559 train and 148 eval clips, 772 MB.
- Median F0 of about 149 Hz (high end for a male voice).
- One unknown symbol, U+0303 (combining tilde).
- Two listening clips are in `outputs/`. **The user has not yet approved the voice.**

Waiting on the user:
1. **Data source:** keep DailyTalk, or add Dewayne Noel / Dry Creek Wrangler as a *private, local-only* dataset (agent recommendation: DailyTalk stays the public default).
2. **Code licence** for the repo (MIT or Apache-2.0 suggested). No LICENSE file exists yet.
3. Listening approval of the DailyTalk voice.

## Next steps, in order

1. **Find why real-data training is slow.** A 60-step acoustic benchmark on real data logged no step within 10 minutes, while synthetic data ran at ~0.8 s/step.
   - Profile with `scripts/train.py --stage acoustic --steps 10 --log-every 1 --run <scratch dir>`, timing each part separately: shard loading (`torch.load` of ~470 MB), collate, monotonic alignment (a Python loop over up to ~1,000 frames per batch, on CPU), forward/backward, and `CpuLimiter` sleeps.
   - Likely causes:
     - MPS recompiles kernels for every new tensor shape; real batches vary in length.
     - The CPU alignment loop gets throttled by the 25% cap.
   - Likely fixes:
     - Pad batches to bucketed lengths (e.g. frames to a multiple of 64, tokens to a multiple of 16) to limit shape variety.
     - Lower `batch_frames`.
     - Vectorize or JIT the alignment loop.
     - Exclude alignment from the limiter only if the user agrees.
   - Then benchmark the vocoder stage the same way.
   - Record real seconds/step and memory in `docs/training.md` under "Measured so far".
2. **Small fixes:**
   - Add U+0303 to `oddmouth/text.py` symbols (bump `SYMBOL_VERSION`; re-run prep).
   - Optionally make the vocoder stage skip loading unused acoustic data.
3. **Train the vocoder first.** Run `--stage vocoder` in sessions until `eval_mel_l1` plateaus and `runs/vocoder/samples/` sound clean. GAN losses start at step 2,000.
4. **Train the acoustic model.** Listen to `runs/acoustic/samples/`; check durations and alignment if speech is garbled. Then test `scripts/speak.py` on `docs/eval_prompts.tsv`.
5. **Browser:** export both generators to ONNX, test with ONNX Runtime Web (WASM, then WebGPU), and wire `web/` to real synthesis. Replace the macOS demo WAV only with real Oddmouth output.
6. **Release:** add the LICENSE the user picks. Publish weights only if the data licence allows; DailyTalk commercial use is not cleared.

If the user chooses Dry Creek Wrangler, write `scripts/prepare_dry_creek.py`:
- **Input:** the feed at https://feeds.megaphone.fm/dry-creek-wrangler.
- **Download:** one episode at a time via `oddmouth.cache.write_bounded` (≤1 GB per file), decoded with ffmpeg.
- **Transcription:** Whisper with word timestamps, offline preparation only, under the CPU cap.
- **Cleaning:** cut 2–10 s segments at pauses; drop intro/outro music, ads and other voices; split train/eval by episode.
- **Output:** the same shard format as DailyTalk (`acoustic-N.pt`, `waves-N.pt`, `manifest.json`), so `train.py` works unchanged.
- **Limits:** start with a 15–20 h subset. Keep it local and never publish weights trained on it. A permission-request draft to the creator is in git history (`VOICE_PERMISSION_REQUEST.md`, commit `cd4ed4d`). Do not send anything on the user's behalf.
