# Oddmouth research scope and unresolved experiments

Checked on 21 November 2026. The main deliverable is `VOICE_MODEL_PLAN.md`; its links point to primary papers, official repositories, model cards, and dataset publishers.

## What was checked

- The workspace was empty apart from Git metadata. No existing application or model was modified.
- Read research material for StyleTTS 2, Matcha-TTS, F5-TTS, CALM, Qwen3-TTS, and M5-TTS; examined current inference/training release documentation.
- Verified Pocket's small model against its actual public YAML: 15.6M flow LM plus 2.6M decoder. The YAML points to separately versioned cloning and non-cloning checkpoints. Those weights were not downloaded.
- Checked Kitten Micro's 40M card and Kitten 2 Nano's card/file listing. The latter lists English ONNX files at 17.4 MB INT8 and 8.83 MB INT4, plus separate voice and frontend assets. Those file sizes are not a complete application budget.
- Read HiFiTTS-2's raw dataset card, including metadata fields and selective-download implications. No bulk audio or dataset archives were downloaded.
- Read Matcha's actual comparison table: the 18.2M acoustic network and 13.9M vocoder are separate. The combined 32.1M figure is arithmetic from that published configuration.

## Licensing distinctions that affect the decision

Pocket's code repository identifies MIT, while the currently inspected [weight card](https://huggingface.co/kyutai/pocket-tts) identifies CC BY 4.0 and presents access/use conditions for cloning weights. Do not describe the entire stack as simply MIT. For a fixed public voice deployment, inspect the exact chosen checkpoint, voice asset, and redistribution terms; do not put a Hugging Face credential in frontend code.

[Kitten 2 Nano](https://huggingface.co/KittenML/kitten-tts-2-nano) and [Micro 0.8](https://huggingface.co/KittenML/kitten-tts-micro-0.8) identify Apache-2.0 on their cards. The [current general Kitten repository](https://github.com/KittenML/KittenTTS) warns that models are licensed separately; its larger 1.7B KittenTTS 2 points to a different community license. Do not transfer permissions from a small model to the large model or infer cloning support in Nano from a family-wide feature list.

[F5-TTS](https://github.com/SWivid/F5-TTS#license) explicitly separates MIT code from CC-BY-NC pretrained weights. [StyleTTS 2](https://github.com/yl4579/StyleTTS2) publishes training and fine-tuning code, but pretrained-model usage provisions and dependencies must also be inspected before adopting a checkpoint. The plan does not treat a repository-level license as proof of every weight/data/voice grant.

[M5](https://github.com/ASLP-lab/M5-TTS) releases inference/checkpoints and states training, continued-pretraining, and GRPO training code are not included. Its per-artifact license references need resolution before product adoption.

## Outstanding before implementation commitment

1. Listen to candidates: naturalness, depth, older character, and consistency have not been established by this research.
2. Select an actual free-data male speaker and count clean usable hours. No speaker ID is recommended without auditioning; dataset availability alone does not establish voice suitability.
3. Prove the exact small model can be adapted and exported. Pocket teacher fine-tuning and six-layer distillation documentation do not establish a turnkey trainer for the distinct 18.2M architecture.
4. Resolve the exact checkpoint/voice/frontend distribution inventory and pin revisions and hashes before building.
5. Reproduce a browser path for each finalist. Pocket's upstream README lists community browser ports, but the linked KevinAHM export repository returned 404 in this check. Do not depend on that particular port being available. An independently validated port/export is required.
6. Benchmark supported devices. Published CPU/GPU speed claims are not browser measurements and give no thermal/battery guarantee.
7. Conduct a matched human test before saying the output matches ElevenLabs. No such claim is established here.

## Definition of research completion

The research request is fulfilled by a basic explanation, current technical shortlist, free-data sources, concrete training and browser routes, acceptance criteria, and a staged resource plan. Training, bulk data collection, creating a website, paying for compute, and generating recordings are subsequent implementation work; they were not performed as part of this planning request.
