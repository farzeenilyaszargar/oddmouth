# Oddmouth research scope

Updated 21 November 2026. The current decision is **single-speaker training from scratch, including the vocoder, with no emotion controls**. The earlier pretrained adaptation/teacher recommendation has been superseded.

The [model plan](VOICE_MODEL_PLAN.md) identifies relevant primary papers and the [Mac system plan](MAC_TRAINING_SYSTEM.md) specifies implementation phases and resource limits. Algorithms and appropriately licensed source code can be reused; pretrained speaking weights, other-speaker training data and synthetic teacher speech are excluded.

Research reviewed compact flow-matching models, phoneme/duration/prosody supervision, waveform GAN training and browser runtimes. Published model sizes and speed figures are reference evidence, not measurements of Oddmouth or this M2 Mac. Exact dependency versions, model implementation sizes and backend operator compatibility must be pinned and tested during implementation.

The selected speaker is Dewayne Noel. Listening preference is settled; clean single-speaker duration, transcript coverage and recording/model-distribution rights remain unverified. Episode runtime is not training duration. Emotion coverage is no longer an acceptance criterion.

Remaining experiments: random-initialized module construction and complete parameter count; MPS forward/backward and browser export checks; reliable alignment and tiny-set learning; scratch acoustic training; separate scratch vocoder training with measured discriminator memory; integration and unseen-text listening; bounded full-corpus passes; browser performance and quantization checks.

The planning tools do not download recordings, load checkpoints or train speech. No custom voice quality, training throughput or browser synthesis has yet been demonstrated. Training time must be estimated separately for acoustic and vocoder phases after real benchmarks.
