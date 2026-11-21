# Oddmouth: single-voice training from scratch on the Mac

Updated 21 November 2026. This document supersedes the earlier pretrained-adaptation and emotion-control plans. It is a plan, not an implemented trainer or a measured quality result.

## Fixed scope

- Train one voice: Dewayne Noel / Dry Creek Wrangler, the user's selected delivery.
- Initialize **every deployed neural component randomly**, including the text encoder, acoustic generator, duration/prosody predictors, and vocoder. No pretrained TTS or vocoder checkpoints, fine-tuning, teacher distillation, synthetic teacher data, or other-speaker training audio.
- No emotion tags, emotion embeddings, emotion classification labels, or emotion-specific acceptance tests. Learn the speaker's natural conversational rhythm, emphasis, and pauses directly from recordings.
- Keep the complete deployed neural pipeline below 50M parameters and target browser-only generation with no provider character quota.
- Download audio only when necessary, with at most 1,000,000,000 bytes per chunk. No voice audio was needed or downloaded for this revision.

From scratch means the speaking model learns pronunciation, timing, and sound production from this one speaker's text/audio pairs. It does not require inventing every algorithm or avoiding open-source code. Existing papers and licensed implementations can inform the architecture without loading their learned weights. A pretrained recognizer may help produce transcripts offline; its weights and representations do not initialize or condition the deployed model. Manually transcribed data is an alternative.

## Architecture in basic terms

The text frontend turns text into phonemes. A text encoder learns their relationships. Duration and prosody predictors learn how long sounds last and how pitch and energy vary. A conditional flow-matching network generates a mel spectrogram, a compact description of sound over time. A separately trained vocoder converts that description into audible samples.

Use deterministic text normalization and an offline/browser phonemizer, with its language assets and licence tracked. Avoid a learned language model in the deployed frontend. Use one implicit speaker identity: no speaker selection or speaker embedding network.

The primary proposal is a compact flow model with a HiFi-GAN-style vocoder, all randomly initialized. [Matcha-TTS](https://github.com/shivammehta25/Matcha-TTS) supplies a useful reference for flow matching and monotonic alignment; [HiFi-GAN](https://github.com/jik876/hifi-gan) supplies a reference for waveform generator/discriminator training. [FastSpeech 2](https://arxiv.org/abs/2006.04558) motivates explicit duration, pitch and energy supervision. This combination is an engineering proposal, not an already validated upstream configuration.

| Deployed component | Proposed design |
|---|---|
| Text frontend | Deterministic normalization, phoneme inventory up to 512 symbols |
| Text encoder | Four blocks, width 256, feed-forward width 1,024 |
| Duration and prosody | Small duration, pitch, and energy heads; measured training targets |
| Acoustic flow network | Twelve blocks, width 384, six heads, feed-forward width 1,536; self-attention and text cross-attention |
| Conditioning | Text, predicted timing/prosody, flow time; fixed positional encodings |
| Waveform generator | HiFi-GAN-style generator, budget reservation 13.9M parameters, trained on this speaker |

The analytic estimate is **46,409,523 parameters including the vocoder reservation**, leaving about 3.59M headroom. The sizing utility explicitly counts projections, biases, norms, and heads. The vocoder allocation is a reservation, not a count of implemented weights. Any extra prior-mel or prosody conditioning projections must fit within the headroom and be included in the eventual count. Count actual loaded modules and the exported graph before accepting the design. Discriminators and offline alignment/recognition tools are training-only and must not ship.

A 50M ceiling is not a requirement to fill all 50M slots. If the full proposal is too costly on this Mac, reduce flow depth/width before the long scratch run and regenerate the budget; the smaller model still starts from random weights. Do not silently replace scratch training with pretrained adaptation.

## Audio conventions and data

Use 22,050 Hz mono, 80 mel bins, FFT/window 1,024, hop 256, frequency range 0–8,000 Hz, and one documented log-mel implementation. Define normalization using training data only and apply the identical convention to the acoustic model and vocoder. These settings are a starting design choice, not inherited checkpoint constraints. Never mix feature definitions between stages. Higher-rate audio can be considered later; upsampling does not recover detail.

The selected source inventory lists 209 episodes with **87:03:34 programme runtime**, not verified clean training speech. Measure usable single-speaker hours after removing advertisements, music, overlap, clipping, duplication, other speakers and excessive noise. Prefer more than 50 clean hours as requested; do not substitute total show duration for that target. No other speaker is added to improve coverage. Recording and distribution rights remain unverified; see [the source plan](DEWAYNE_TRAINING_PLAN.md).

Prepare 2–6 second utterances initially, with correct transcript/word boundaries. Preserve meaningful pauses and emphasis. Never use a full transcript with an arbitrary cropped waveform. Split whole episodes/sessions approximately 90/5/5 into train/development/test and deduplicate before training. Freeze the test split. Keep provenance, source offsets, hashes, corrected transcripts, sample rate, feature version and split assignment in small manifests. Emotion annotation is not part of preparation.

A 20–60 minute pilot diagnoses the pipeline; it is not enough evidence that a model trained from zero generalizes. After the pipeline works, expand to several hours for coverage, then the full verified corpus. Evaluate held-out words, numbers, names, punctuation and longer sentences to expose gaps in one speaker's vocabulary.

## Mac execution and memory

The inspected machine is an **M2 MacBook Air with 8 GiB unified memory**, with roughly 15 GiB free storage at the previous inspection. It was already using substantial swap. The regenerated [preflight report](reports/mac_training_preflight.json) is a snapshot, not a training benchmark. It excludes serial numbers and hardware UUIDs.

Train acoustic and waveform stages separately, unloading one before loading the other. The acoustic stage does not require a vocoder in memory. The vocoder stage uses recorded waveform/mel pairs, not a simultaneously loaded acoustic model. This allows both components to be trained from scratch without maintaining both training graphs at once.

Start with FP32, microbatch 1, gradient accumulation 16, loader workers 0, pinned memory off, short utterances, and gradient clipping 1.0. Acoustic AdamW LR 1e-4 with warmup is a proposal to tune from scratch, not the former low-rate adaptation setting. Tune vocoder generator/discriminator optimizer settings separately using the referenced implementation as a starting point. Count updates after accumulation, and reset neither optimizer nor schedule at each shard.

For the proposed architecture, acoustic parameter/gradient/two-moment storage is about 520 MB; the vocoder generator alone needs about 222 MB of equivalent FP32 Adam storage. **Neither number includes activations, training-only discriminators, runtime allocations, copies, or other apps.** Profile discriminators explicitly; their cost is not bounded by the deployed 50M ceiling. Use approximately 8,192-sample waveform segments initially (about 0.37 seconds), then benchmark longer segments if quality and memory permit. Match segment padding and STFT conventions carefully.

Create a pinned Python 3.11 project environment rather than assuming the installed Python 3.14 fits older dependencies. Validate arm64 native extensions and MPS support on tiny inputs before installing a large stack. Test alignment, attention, convolution, STFT and gradients independently. Keep unsupported feature/alignment operations on CPU deliberately; do not hide a whole-model CPU fallback. [PyTorch MPS documentation](https://docs.pytorch.org/docs/stable/notes/mps.html).

Do not run transcription, acoustic training and GAN training concurrently. Mixed precision and activation checkpointing are optional experiments after stable FP32 learning, not assumed solutions. Close unnecessary apps before sustained runs; tooling must not terminate personal apps. An optional larger GPU can use the same randomly initialized recipe if later requested, without changing the browser-only inference goal. Full scratch training on this fanless 8 GB Mac may be slow; feasibility and duration require measurements, and ElevenLabs parity is not promised.

## Training stages from random initialization

1. **Implementation and export checks.** Build the modules with explicit random seeds and no checkpoint-loading path. Count all deployed parameters. Test one forward/backward update and a synthetic browser export for each inference component. Random output is expected here: this checks operators and wiring, not speech quality. Pin code, dependency and phonemizer versions and audit their licences.
2. **Data/alignment diagnostic.** Prepare the multi-session pilot. Train a text-to-mel prior and monotonic alignment from the paired recordings; use prior reconstruction/likelihood and duration objectives to establish correspondence. Matcha's implementation is a reference, not proof that alignment will emerge in this custom network. Visualize paths for monotonicity, coverage and skipped phones. Optionally use offline forced alignment to supervise durations, with manually checked boundaries; this is a preparation tool, not pretrained initialization. Do not lock unreliable durations into the full corpus.
3. **Scratch acoustic training.** Train the text encoder, duration/prosody heads, prior and conditional flow network. Optimize flow velocity regression plus duration/prior losses and masked pitch/energy losses with documented scaling. Use ground-truth durations/prosody initially, then test predicted values and exposure mismatch. Pitch requires voiced/unvoiced masking. Overfit 8–16 clips briefly to detect bugs; then use multi-session data and monitor development learning. Extend alignment before changing architectures if the problem is bad correspondence.
4. **Scratch waveform training.** Randomly initialize the vocoder generator and its training-only discriminators. Train on this speaker's real mel/waveform pairs, using reconstruction and adversarial/feature-matching objectives from the chosen recipe. Begin with a reconstruction diagnostic before enabling the full adversarial workload. Monitor generator/discriminator balance, buzzing, pitch fidelity, noise and amplitude. An untrained vocoder cannot be frozen and treated as a functional sound generator.
5. **Integrate the two trained components.** First listen to the vocoder reconstructing held-out real mels to isolate waveform quality. Then synthesize held-out text through the learned acoustic model and vocoder. If predicted-mel mismatch causes artifacts, generate paired predicted-mel training examples offline, aligned to recordings using known durations, and calibrate the already scratch-trained vocoder on those pairs. Do not align an arbitrary generated utterance to unrelated waveform timing. Run components sequentially to preserve memory.
6. **Long-form quality and browser optimization.** Evaluate unseen text, voice consistency, natural delivery, pauses, pronunciation, repetitions/omissions and ten-minute narration. Compare 2/4/8 flow steps, then test selective quantization. There are no emotion-tag tests. Only export inference modules after checking native/browser parity and quality.

Acoustic and vocoder stages can alternate between saved checkpoints during development, but neither is initialized from externally pretrained weights. A small pilot may produce poor speech while alignment and pronunciation are still being learned; diagnose losses and held-out reconstruction rather than treating immediate naturalness as a prerequisite for scratch training.

## Bounded data rotation and disk

Maintain the user's maximum download size of **1 GB decimal** and an additional **1 GB combined managed-data cache**. Default concurrent allocations are: active features 450 MB; fixed evaluation data 100 MB; replay examples 100 MB; current compressed source portion 100 MB; temporaries 200 MB; metadata 50 MB. These sum to 1 GB, not six separate allowances.

The [bounded writer](scripts/bounded_cache.py) enforces actual per-file and aggregate bytes, handles unknown-size streams, serializes cooperating writers, checks a 5 GB free-disk reserve, and removes failed partial writes. It has no network capability. The future scheduler must also enforce each allocation and use bounded writes for decoder outputs. No unchecked subprocess output, whole-episode PCM expansion, or parallel unbudgeted prefetch. If a source cannot be retrieved with supported smaller files/ranges inside the cap, report it rather than fetching an oversized file first.

Fifty hours of mono PCM16 is about 7.94 GB; FP16 mel payload is about 2.48 GB. The full corpus must rotate through cache. During acoustic training retain mels and compact prosody/duration features. During waveform training replace some feature capacity with paired waveform segments; 450 MB no longer represents nine hours of paired examples. Re-fetch/reprocess evicted source material as needed. Maintain separate phase-specific shard manifests, preprocessing hashes and corrections so each pass uses consistent examples.

Shuffle shards and utterances on each whole-corpus pass. Preserve optimizer state across shards. Use a bounded replay reservoir, proposed 20% sampling, across earlier sessions to reduce forgetting; balance recording sessions and phonetic coverage, not emotions. Do not train to convergence on one chunk and restart on the next. Fixed evaluation material remains independent of shard rotation. If a remote source disappears, exact reconstruction of an evicted shard may become impossible; keep provenance and report that limitation.

Code/tools, model checkpoints and exports are outside the data-cache cap, but not outside physical disk limits. Allow 2–4 GB for environment/tools, up to 3 GB for phase checkpoints plus atomic-save temporary space (including vocoder discriminator/optimizer states), and about 0.5 GB for logs/export trials. These are provisional allowances: measure actual checkpoint sizes and refuse saves that would breach the 5 GB reserve. Retain one resumable checkpoint for each stage and a best final inference export; do not keep a separate archive of every epoch. No pretrained speech-weight download allocation is needed. Never delete personal files or put bulk data/weights in Git.

Checkpoint models, optimizers, schedulers, RNG seeds/state, update counters, phase, shard/sample cursor, replay membership, data/config/frontend versions, normalization and any gradient-accumulation state. Prefer saves at optimizer boundaries. A vocoder checkpoint includes both generator and discriminator states; exported inference weights include only the generator.

## Benchmark, decisions, and browser release

Benchmark acoustic and vocoder stages separately: ten warmup updates followed by at least 200 optimizer updates, then a sustained test of at least 20 minutes if memory permits. Record seconds/update including accumulation, peak process/system memory, swap growth, data preparation time and loss/gradient stability. Compare early and sustained throughput. Shrink architecture or waveform segments if needed; stop if pressure grows continuously or disk reserve is threatened.

Compute time only after measuring: `total days = sum(stage_updates × stage_seconds_per_update) / 86400`, plus preprocessing/evaluation. Fifty hours in four-second utterances is roughly 45,000 examples or 2,813 updates/pass at effective batch 16 before replay. Waveform training has a different segment/sample workload; do not reuse the acoustic epoch estimate for it. Required passes are determined by convergence, not the size of a download chunk.

Before release, require stable training, reasonable alignment, intelligible unseen text, faithful held-out real-mel reconstruction, recognizable target timbre, natural narration and acceptable long-form failure rates. Use [the fixed evaluation texts](VOICE_EVALUATION_PROMPTS.tsv) and human listening; no quality parity is established by this plan.

Export acoustic/vocoder modules to ONNX, test WASM and then supported WebGPU operators in actual Safari/Chromium browsers. A random-weight early export verifies compatibility; a trained-weight export must verify sound. Use a Web Worker, bounded phrase audio queues and Web Audio playback. Phrase-wise generation is not a claim of causal token streaming. Cache versioned weights/frontend/runtime assets for offline use and export long WAV recordings incrementally. [ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/) documents backend coverage differences; quantized export requires new quality and performance tests.

The model only speaks text. Conversation reasoning would be a separate system. Unlimited local use means no provider character quota, while device speed, storage, power and applicable licences still matter.

## Current artifacts

Implemented: planning configuration, analytic budget/report generator, bounded write helper and storage/scope checks. Not implemented: speech modules, acquisition scheduler, alignment/transcription pipeline, scratch trainer, trained checkpoints or browser synthesis. No voice recordings were downloaded and no training was started. The immediate implementation task is random-initialized module construction, parameter counting and MPS/export smoke tests, followed by the bounded pilot.
