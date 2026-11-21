# Oddmouth model plan

> **Superseded 21 November 2026** by the 15M design in [MAC_TRAINING_SYSTEM.md](MAC_TRAINING_SYSTEM.md) and the DailyTalk data choice in [DATA_SOURCE.md](DATA_SOURCE.md). Kept for history.

Revised 21 November 2026 to follow the user's current requirements. This replaces the earlier pretrained-model adaptation recommendation.

## Product and training contract

Build a single-speaker generative text-to-speech model **from scratch**. Randomly initialize all deployed neural components, including the vocoder, and train only on the selected speaker's recordings. Do not use pretrained TTS weights, pretrained vocoder weights, fine-tuning, a teacher/student pipeline, synthetic teacher speech or other-speaker pretraining.

The chosen voice is Dewayne Noel / Dry Creek Wrangler. Learn naturally engaging YouTube narration and conversational delivery. Explicit emotion controls have been removed: no happy/angry tags, emotion embeddings or annotation requirements.

The complete browser inference model must stay below 50M parameters, including the waveform generator. Target offline generation after initial asset installation, with no server inference or provider character quota. ElevenLabs is a quality aspiration, not an established result.

## Primary design

Use a phoneme frontend, small text encoder, duration/prosody prediction, conditional flow-matching acoustic generator, and separately scratch-trained HiFi-GAN-style vocoder. One implicit speaker; no voice selector or speaker encoder. The analytic proposal totals about 46.41M parameters with a 13.9M vocoder reservation; actual implementation must be counted.

The authoritative detailed plan is [MAC_TRAINING_SYSTEM.md](MAC_TRAINING_SYSTEM.md). It covers architecture, alignment from paired data, acoustic losses, waveform adversarial training, integration, checkpoints, 1 GB bounded data rotation, M2/8 GB memory settings, benchmarking and browser export. [configs/mac_training.json](configs/mac_training.json) records the current machine-readable scope.

Train acoustic and waveform components in separate phases to reduce memory pressure. Both start randomly. Temporarily unloading a component is a memory strategy, not permission to substitute a pretrained one. Small pilots diagnose the implementation; full one-speaker corpus coverage is needed to judge generalization.

## Research basis and boundaries

- [Matcha-TTS paper](https://arxiv.org/html/2309.03199v2) and [implementation](https://github.com/shivammehta25/Matcha-TTS): compact flow matching and alignment ideas. Reuse licensed code/algorithms where useful, without loading checkpoints.
- [HiFi-GAN](https://github.com/jik876/hifi-gan): reference for training a waveform generator with training-only discriminators. The generator ships; discriminators do not.
- [FastSpeech 2](https://arxiv.org/abs/2006.04558): duration, pitch and energy supervision from recorded speech.
- [StyleTTS 2](https://github.com/yl4579/StyleTTS2), [F5-TTS](https://github.com/SWivid/F5-TTS), [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) and [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) remain background research, not selected checkpoints, teachers or training dependencies.

A pretrained recognizer/forced aligner can assist offline transcript and boundary preparation only; no learned speech representations or weights transfer into Oddmouth. Every deployed learned component remains trained from scratch on the one speaker. If avoiding even preparation tools is desired later, manually corrected transcripts and training-derived alignment provide the alternative.

## Data and evidence

[Source research](DATA_SOURCE.md) records the selected voice and rejected reading-style candidates. The podcast inventory lists 87:03:34 across 209 episodes, not verified clean speech. Audit usable hours, transcripts, single-speaker consistency and recording rights. The preferred target remains more than 50 clean hours. Do not add another speaker to fill a shortfall.

Necessary downloads are allowed only in chunks no larger than 1,000,000,000 bytes. Planning requires none. Preserve a 1 GB combined data cache and a separate disk reserve as specified in the Mac plan.

Success requires measured trainability, unseen-text intelligibility, recognizable voice, natural timing, long-form stability and real browser performance. No quality or training-time guarantee exists before those experiments. All completed project updates are committed and pushed to the Oddmouth repository.
