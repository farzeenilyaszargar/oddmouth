# Oddmouth: architecture and training on this Mac

Updated 21 November 2026. This is an implementation plan, supported by a hardware inspection, upstream code review, analytic sizing, and tested storage utilities. It is not a trained model, a completed MPS port, or a measured quality claim. No voice audio was downloaded for this work.

## Recommendation in basic terms

Start with a small model that already knows how to pronounce English. Adapt its delivery to the selected voice, then teach explicit emotion controls using recordings that actually demonstrate those emotions. Keep its existing sound generator fixed initially. Training every component from nothing would spend this Mac's limited resources relearning pronunciation and sound production.

The system has three parts: a text reader converts words into pronunciation and timing; a conditional speech generator creates a compact description of sound; a vocoder turns that description into the waveform you hear. A tag such as `[happy]` changes the generator's conditioning. Merely removing the tag from the text does not teach happiness.

Use a pretrained Matcha-style system for the first experiment, approximately **32.1M parameters including its published vocoder**. Only consider the expanded **46.46M** design below if experiments show a reason to add capacity. Both remain research candidates for the target voice and emotion controls. ElevenLabs parity is an aspiration, not a demonstrated outcome.

## Observed hardware and practical limits

The inspection found an Apple M2 MacBook Air, eight CPU cores, **8 GiB unified memory**, and roughly **15 GiB free storage**. The saved snapshot shows approximately 7.3 GiB of swap already in use; free space and memory pressure vary with other applications. See the sanitized [preflight report](reports/mac_training_preflight.json). It contains no serial number or hardware UUID.

This computer can be used for corpus preparation and small adaptation experiments, subject to a real forward/backward benchmark. Its shared memory and fanless sustained performance make full training from scratch a poor first choice. Close unnecessary applications yourself before a pilot; the tooling will not terminate them. Do not start transcription and model training together.

An optional larger GPU could later shorten experiments, but the product still runs locally in the browser. No hosted inference service is part of this design. No training duration is promised before benchmarking this Mac.

## Architecture decision and parameter budget

| Candidate | Complete size | Decision |
|---|---:|---|
| Published Matcha acoustic model plus published vocoder | Approximately 18.2M + 13.9M = 32.1M | First adaptation experiment; verify the exact checkpoint and licence |
| Expanded conditional flow design below | Analytic 46,460,083 | Later experiment; no matching pretrained checkpoint is established |
| Pocket TTS small configuration | Upstream configuration describes 18.2M total | Research alternative; training portability and emotion adaptation remain unresolved |

The [Matcha paper](https://arxiv.org/html/2309.03199v2) reports the baseline sizes. Its [official implementation](https://github.com/shivammehta25/Matcha-TTS) provides a training starting point. Pocket's [small configuration](https://github.com/kyutai-labs/pocket-tts/blob/main/pocket_tts/config/english_18m_2026-10.yaml) is attractive for inference, but its [training guide](https://github.com/kyutai-labs/pocket-tts/blob/main/training/README.md) targets Linux and NVIDIA, with substantially greater training memory requirements than this Mac. A small inference model is not evidence of a turnkey small-memory trainer.

For the expanded proposal: a 512-symbol phoneme vocabulary, four 256-wide text blocks, duration and pitch/energy prediction, eight emotion embeddings, and twelve 384-wide flow blocks with six attention heads. Each flow block has self-attention, cross-attention, and a 1,536-wide feed-forward layer. Reserve 13.9M parameters for the vocoder. Emotion and time embeddings are added to conditioning rather than creating a second large language model. Positional encodings should be fixed, with no hidden large learned tables.

The [sizing script](scripts/plan_training.py) includes projections, biases, normalization, timing/prosody heads, and the vocoder reservation. Its 46.46M count is analytic: the vocoder reservation is not a count of loaded weights. It leaves about 3.54M parameters of headroom. Actual implementation must count every deployed learned component, including any learned frontend, adapters, and vocoder. Training-only recognition, alignment, or discriminators are excluded only if they are absent from deployment. A wider custom design cannot directly load differently shaped baseline weights; it would require explicit weight transfer, distillation, or separate training. This is why it is not the first experiment.

Weights alone would be approximately 186 MB in FP32, 93 MB in FP16, or an idealized 46.5 MB in INT8 before format overhead. Quantization does not reduce the parameter count and may affect sound. Adam parameters, gradients, and two moments for the expanded non-vocoder portion are about 521 MB; frozen vocoder weights add about 56 MB. **These figures omit activations, runtime allocations, copies, and other applications** and cannot establish that training fits.

Use **22,050 Hz, 80 mel bins, FFT/window 1,024, hop 256** for the initial checkpoint-compatible experiment. The [upstream data configuration](https://github.com/shivammehta25/Matcha-TTS/blob/main/configs/data/ljspeech.yaml) also specifies frequency limits and normalization. Match all of those conventions to the chosen acoustic/vocoder weights; estimate target-data statistics only with a deliberate compatible normalization strategy. Do not substitute a 24 kHz frontend or claim that resampling improves fidelity. A later 24 kHz version needs compatible weights or additional training.

## Data source and unresolved coverage

The selected source is Dewayne Noel / Dry Creek Wrangler, using original podcast/channel material, not third-party edits. The metadata inventory contains **209 episodes and 87:03:34 programme runtime**. This is not verified clean single-speaker duration. Ads, music, other voices, duplication, and noise may reduce it considerably. See [the catalogue](reports/dry_creek_catalogue.json) and [source record](DEWAYNE_NOEL_SOURCE.md).

Rights remain unverified. Death does not itself eliminate copyright or establish public-domain status; the ownership discussion and primary legal sources are in [the voice preparation plan](DEWAYNE_TRAINING_PLAN.md). No contact message has been sent. This planning update neither establishes a training licence nor claims one is unnecessary.

Before substantial training, audit several sessions for clean, naturally expressive speech. Record audible happy/angry coverage separately from conversational storytelling. A lesson about anger is not necessarily angry delivery. Human-review emotion labels and retain an uncertain category; do not manufacture missing emotions by assigning tags. If angry examples are absent, the honest choices are to acquire suitable authorized examples, test transfer from suitably licensed expressive data, or defer that capability. Pitch shifting alone does not supply realistic emotional performance.

## Hard download and working-storage limits

The user's updated instruction allows downloads **only when necessary**, with a maximum chunk of **1,000,000,000 bytes**, using decimal GB. No voice download is necessary to finish planning. For eventual preparation, apply an even stricter default raw-file allowance of 100 MB and a **1 GB combined managed data cache**:

| Concurrent allocation | Bytes |
|---|---:|
| Active training features | 450,000,000 |
| Fixed evaluation clips/features | 100,000,000 |
| Replay examples across shards | 100,000,000 |
| Current compressed source portion | 100,000,000 |
| Decoding and preparation temporaries | 200,000,000 |
| Metadata, transcripts, labels and indices | 50,000,000 |
| **Total** | **1,000,000,000** |

These are allocations within one cap, not independent gigabytes. The present helper enforces the aggregate and per-file limits; a future scheduler must enforce the individual allocations too. Allow no unbudgeted parallel prefetch. Unknown Content-Length is not permission to grow without bound. Count bytes while reading; reject excess before writing. When a source exceeds its allocation, use supported range/segment retrieval or a different smaller source. A source that cannot be retrieved within the constraints must be reported as unavailable, rather than downloaded in full first.

Stream-decode short clips rather than expanding an hour of PCM into RAM or temporary disk. Fifty hours of mono PCM16 at 22.05 kHz is about **7.94 GB**; FP16 80-bin mel features alone are about **2.48 GB**. A 450 MB feature shard holds at most roughly nine hours before other features and headers. The full corpus therefore rotates through storage; it never fits all at once in the cache. Processing buffers must also be bounded, for example 1 MiB network reads, and feature writers must use the same accounting path.

The implemented [bounded writer](scripts/bounded_cache.py) serializes cooperating writers, counts actual bytes, refuses replacement of existing files, rejects cache symlinks, checks a 5 GB free-disk reserve, and removes its own partial file on failure. It performs no networking. All future raw, temporary, and feature writes must use it or equivalent coordinated accounting; external programs writing directly into the cache are outside its protection. Decoder subprocess output must therefore be piped into a bounded writer, not an unchecked output file.

Dependencies, pretrained weights, checkpoints, and logs are **outside the 1 GB data-cache cap**, but still consume disk. Reserve roughly 2–4 GB for the environment/tools, up to 1 GB for selected pretrained artifacts, around 1.5 GB for last full checkpoint + best weights + atomic-save temporary, and up to 0.5 GB for logs/export trials. These are planning allowances, not measured install sizes. Maintain at least 5 GB free after each operation. With only about 15 GiB initially free this is tight: inspect actual sizes before installing or saving, clean only regenerable project artifacts, and pause if reserve cannot be maintained. Do not delete personal files or rely on swap space as spare RAM.

## Preparation and training sequence

1. **Reproducible environment and compatibility test.** Create a project-local Python 3.11 environment with `uv`, pin a tested PyTorch release and upstream commit, and record the dependency lock. The installed system Python 3.14 is not assumed compatible with older dependencies. Check `torch.backends.mps.is_available()`. Test text processing, mel extraction, alignment, a forward pass, loss, backward pass, and optimizer update on a tiny batch. Keep audio transforms/alignment on CPU when needed; move only supported tensors to MPS. Matcha's training code invokes monotonic alignment, which needs explicit CPU/native-extension testing on arm64. Fix operator/dtype issues deliberately; do not silently route the whole model through CPU fallback or disable allocator protections. [PyTorch MPS documentation](https://docs.pytorch.org/docs/stable/notes/mps.html).
2. **Export smoke test before a long run.** Load the exact baseline, count its parameters, synthesize short text, export acoustic and vocoder components, and run them in a real browser. Discover unsupported operators early. Review code, checkpoint, data, and redistribution licences separately. Pin hashes of the exact artifacts; this plan intentionally has not fetched weights or invented a validated checkpoint revision.
3. **Small multi-session pilot.** Prepare 20–60 minutes from several original solo episodes. Decode mono audio, inspect clipping/background music, transcribe, align words, and retain utterances of about 2–6 seconds. Use word boundaries when splitting: never pair a four-second audio crop with the uncut transcript. Keep speaker/session IDs, source offsets, transcript corrections, emotion confidence, and processing versions in a manifest. Run small MLX Whisper transcription as a separate phase; compare a small English model against manual samples before scaling. [Official MLX Whisper example](https://github.com/ml-explore/mlx-examples/blob/main/whisper/README.md).
4. **Create holdouts before optimizing.** Split whole episodes/sessions, approximately 90% train, 5% development, 5% final test where enough sessions exist. Deduplicate across splits. Keep fixed, auditable evaluation material in the cache; never use the final test to tune settings. Save human transcript/emotion corrections in small versioned manifests. Do not put bulk audio into Git.
5. **Verify learnability.** Briefly overfit 8–16 training clips to diagnose bad transcripts, alignment, mel conventions, or broken gradients. Then train on the multi-session pilot and assess held-out speech. Begin with a frozen vocoder and text encoder; adapt duration/prosody and acoustic generation. Unfreeze text layers at a lower rate only if pronunciation or identity adaptation needs it. A mismatch in male-voice reconstruction through the frozen vocoder is a reason to reconsider that checkpoint, not to train for days blindly.
6. **Mac settings.** Start FP32, microbatch 1, accumulate 16 microbatches per optimizer update, loader workers 0, pinned memory off, approximately four-second utterances, gradient clipping 1.0. AdamW learning rate 1e-5 and weight decay 0.01 are starting proposals to tune, not established optima. Test mixed precision and activation checkpointing separately only after stable numerics. Accumulation reduces activation memory per microbatch, not optimizer-state memory. Avoid GAN/vocoder retraining and concurrent teacher inference in the first 8 GB experiment.
7. **Teach explicit expression.** Add small emotion embeddings and conditioning without changing the baseline's widths. Initialize so neutral behavior remains close to the pretrained model, then train with human-reviewed tags and balanced sampling. Keep content and identity consistent across tags. Neutral/happy/angry are the first required controls; extra states are reserved, not automatically supported. Follow [the tag specification](EXPRESSION_CONTROLS.md), preserving active tags across sentence chunks. Training pitch/energy targets requires adding those measured features and losses deliberately, not merely having parameter reservations in a sizing script.
8. **Expand only after pilot gates.** Progress to around two clean hours, then the verified usable corpus. Keep preprocessing and training as separate memory phases. Freeze the vocoder so cached mels suffice for most acoustic updates. Convert stored FP16 features back to the chosen training dtype as needed. Feature compression saves disk; it does not prove lower training RAM.

For the full corpus, iterate bounded feature shards in a seeded shuffled order and shuffle examples within each shard. Preserve one optimizer across shards and repeated whole-corpus passes. Do not converge on one episode, delete it, and start a fresh optimizer for the next. A proposed 20% replay fraction samples a bounded reservoir balanced across earlier sessions/emotions to reduce forgetting. Save replay membership and random seeds. Evaluate against the same holdout after each global pass.

With no full local archive, repeated passes may require re-fetching and recomputing evicted features. Keep source URLs, timestamps, content hashes and transformation versions; retain corrections and index manifests after eviction. If a remote source disappears, exact resumption may be impossible. An optional authorized external archive could reduce repeated processing, but is not assumed to exist and does not authorize extra local downloads.

## Checkpoints, benchmark, and decision gates

Save model state, optimizer/scheduler state, RNG state, optimizer update and accumulation position, shard/example cursor, replay membership, tokenizer and audio-statistics versions, config hash, dataset manifest hash, and pretrained-artifact hashes. Prefer checkpointing at optimizer boundaries. Keep one full resumable checkpoint and a separate best weights-only export; write atomically with space for the temporary copy. Resume from verified state after interruption. Never commit these artifacts to ordinary Git.

After ten warm-up updates, measure at least 200 optimizer updates with the actual accumulation setting. Record seconds per update, peak process/system memory, swap growth, losses, non-finite gradients, and data preparation time. Compare early speed with speed after at least 20 minutes to reveal sustained thermal behavior. Stop or shrink the workload if memory pressure grows continuously, swapping dominates, or the 5 GB disk reserve is threatened. Smaller batches do not cure all unsupported operations.

Estimate wall time only from that benchmark: `days = optimizer_updates * measured_seconds_per_update / 86400`, plus preprocessing and evaluation. For example, 50 hours split into four-second clips is roughly 45,000 clips; with effective batch 16 that is roughly 2,813 updates per pass before replay. The number of useful passes is determined by held-out convergence. This is workload arithmetic, not a forecast of this Mac's speed.

Required gates are: stable forward/backward on MPS; repeatable tiny-set learning; intelligible unseen sentences; better target-voice similarity on held-out sessions; listener-recognizable happy/angry without wrong words or changing identity; and successful browser generation. Use the fixed [evaluation prompts](VOICE_EVALUATION_PROMPTS.tsv), human listening and an independent transcription check. Track naturalness, identity, emotion, omissions/repetitions, pronunciation, and ten-minute narration consistency. Set release thresholds against the selected baseline and actual listener results rather than promising a numerical quality score in advance.

## Browser delivery and unrestricted local generation

Export only inference components. Use deterministic text normalization and a compact browser phonemizer, with its language assets and licensing tracked. Run acoustic generation and vocoder in a Web Worker, queue sentence/phrase audio, and play through Web Audio; an AudioWorklet can support buffered playback. This is phrase-level incremental playback, not proven token-level streaming from a noncausal model. Maintain tag state and pause control across phrase boundaries, with boundary listening tests.

Compare 2, 4 and 8 flow solver steps for sound and runtime. Validate ONNX CPU/WASM first, then WebGPU on actual target browsers and operators; ONNX Runtime documents broader WASM coverage than GPU subsets. An exported file alone is not evidence of browser support. Quantize selectively and retest especially the vocoder; INT8 convolution support and speed must be measured. [ONNX Runtime Web documentation](https://onnxruntime.ai/docs/tutorials/web/).

Cache versioned runtime assets and weights with a service worker/Cache Storage or IndexedDB as appropriate, permit chunked WAV export, and bound browser audio buffers for long recordings. Test with networking disabled after installation. Record cold load size, first-audio latency, real-time factor, peak memory, and quality after quantization on Safari and Chromium, including a lower-memory device. "Unlimited" means no provider character quota: generation is still limited by device speed, power, browser storage, and any applicable model/data licence. Conversation understanding would require a separate chatbot; this project provides the speaking component.

## What exists and what remains

Implemented here: a machine-readable [planning config](configs/mac_training.json), sanitized hardware/size report generator, cooperative bounded writer, and seven small storage/planning tests. The tests cover exact byte boundaries, unknown-length streams, temporary expansion, disk reserve, interrupted writes, path containment, and oversized configurations. They use tiny synthetic bytes, not voice recordings.

Not implemented: acquisition scheduler, transcription/alignment pipeline, custom speech architecture, MPS training loop, emotion-trained checkpoint, and browser inference integration. The immediate engineering deliverable is the compatibility/export pilot in steps 1–2; only then should necessary small audio acquisition and adaptation begin. The complete sequence above specifies how to proceed without claiming that untested components already work.
