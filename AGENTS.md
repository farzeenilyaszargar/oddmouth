# Oddmouth project instructions

- The project name is **Oddmouth**.
- The canonical repository is https://github.com/farzeenilyaszargar/oddmouth.
- The user has requested that project work be stored in this repository after each update. Commit and push completed updates; report a push failure explicitly instead of implying that work is synced.
- Keep research claims distinct from measured results. Do not claim voice quality, browser performance, or a trained model without evidence.
- Keep secrets, bulk training audio, model weights, and training checkpoints out of ordinary Git. Track their provenance and reproducible acquisition instructions; choose suitable artifact storage when those assets are introduced.
- The user conditionally authorizes voice-data downloads only when necessary, in chunks no larger than 1,000,000,000 bytes. Planning requires no audio download. Use the bounded cache plan in MAC_TRAINING_SYSTEM.md; do not bulk-download the corpus. Streaming a sample for listening is authorized.
- The measured target computer is an M2 MacBook Air with 8 GiB unified memory. Treat MPS trainability, throughput, and browser performance as unmeasured until tested; avoid heavy jobs during severe memory pressure.
- The user rejected Hi-Fi TTS / John Van Stan's audiobook delivery. Prioritize expressive, conversational YouTube presenter-style male speech. More than 50 hours remains preferred; distinguish whole-show duration from verified hours of one speaker.
- Current scope: train every deployed neural component from random initialization on one selected speaker only, including the vocoder. No pretrained TTS/vocoder weights, fine-tuning, teacher distillation, or other-speaker training data. Pretrained transcription tools may be used only for offline data preparation.
- The user also rejected Mark Nelson / plain audiobook reading and has now listened to and selected Dewayne Noel / Dry Creek Wrangler. Voice preference is approved; its 87:03:34 feed runtime is not verified clean training duration or training permission. The user's report that Dewayne died has not been verified; do not infer public-domain status or absence of a rights holder from death.
- Explicit emotion controls have been removed by the user. Do not add emotion embeddings, emotion labels, or happy/angry acceptance gates. Preserve naturally engaging delivery from the selected speaker.
