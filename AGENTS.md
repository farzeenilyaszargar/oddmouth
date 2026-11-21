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
