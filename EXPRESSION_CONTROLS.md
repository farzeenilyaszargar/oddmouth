# Oddmouth expression controls

Requirement added 21 November 2026. **Design specification; no trained emotion controls are implemented yet.**

## Intended behavior

Oddmouth should produce one consistent deep male voice with explicit control over delivery:

```text
[happy] That worked better than I expected!
[angry] We have discussed this three times already.
[neutral] Let me explain what happened.
```

These brackets are performance directions, not words to speak. Identical text must also be testable under different tags, so emotion cannot simply be inferred from positive or negative vocabulary.

For the first training experiment, prioritize `[neutral]`, `[happy]`, and `[angry]`. These are mandatory target capabilities, not claims about a current checkpoint. Subsequent targets are `[sad]`, `[excited]`, `[calm]`, `[curious]`, and `[surprised]` once each has sufficient validated data and passes listening tests.

Emotion tags apply to following speech until the next emotion tag or end of the generation request. A new request starts neutral. No explicit tag means natural conversational presentation with neutral emotional intent, not deliberately flat speech. Tags may change inside a paragraph, preferably at clause boundaries. Never silently claim an unsupported emotion worked: reject it with a clear message before synthesis. Bracketed literal text needs an escape convention in the future parser.

Example of a planned transition:

```text
[happy] We finally found it. [angry] But someone erased the results.
[neutral] Here is what we can recover.
```

Keep **emotions**, **delivery styles**, and **nonverbal events** distinct. Whispering and shouting describe delivery; laughter and sighs are generated events. `[whispering]`, `[shouting]`, `[laughs]`, and `[sighs]` are later-stage targets requiring separate evidence, not automatic capabilities obtained from happy/angry training. A future intensity setting can be explored after basic controls work; do not promise that doubling a number doubles perceived emotion.

## Model design

Parse the user-facing tags into structured, time-aligned conditioning rather than sending bracket words through an ordinary phonemizer. Preserve tag positions during text normalization and browser chunking. Condition the small speech generator using learned emotion embeddings and per-token or per-span control. Use controls appropriate to the chosen architecture: prosody features and acoustic decoder conditioning for a spectrogram model, or conditioning on the causal generator for a codec/continuous-latent model.

The model must learn how emotion changes rhythm, pitch movement, articulation, energy, and voice quality together. Merely increasing playback volume or shifting pitch is not the intended feature. An utterance-global emotion embedding alone cannot establish reliable changes halfway through a sentence; span transitions need suitable training and evaluation.

Small categorical controls are cheap to store—for example, eight 128-dimensional embeddings contain 1,024 learned parameters—but embeddings alone do not teach expression. Conditioning layers, text features, generator, and audio decoder must **all remain inside the complete 50M parameter budget**. Do not add a separate large language model to interpret a small fixed tag vocabulary in the browser.

## What this changes about the data search

A source must contain the chosen speaker performing the requested emotions, with enough varied examples to learn more than a few phrases. Fifty hours of ordinary podcast discussion does not prove that usable anger, happiness, or controlled transitions are present.

Before approving a source, create a coverage table per emotion: usable duration, clip count, unique transcripts, recording sessions, annotation confidence, and audible intensity. Account for overlap and uncertainty; unclassified speech should not be called neutral by default. Human-review emotion labels, since automatic classifiers can confuse loudness with anger or enthusiasm with happiness. Labels describe the audible performance, not the speaker's actual psychological state.

Prefer emotion variation within the same recording setup to reduce the risk that the model learns microphone or room changes as emotion. Include some matched-text performances across emotions when feasible. Split by episode/session and prevent near-duplicate text/audio leakage. Preserve the speaker identity while changing performance.

Chris Fisher / LINUX Unplugged remains only a raw source candidate. Neither 50 usable single-speaker hours nor happy/angry coverage has been verified. Hi-Fi TTS's previously rejected voice remains rejected. No audio acquisition is authorized.

If the selected free source lacks an emotion, the honest options are to find a better source, obtain additional authorized performances by the same speaker, or test properly licensed teacher-generated supplementation. Synthetic augmentation is an experiment; it can alter the identity or amplify teacher artifacts. Do not substitute another person's voice just to fill an emotion category.

## Validation before exposing controls

- Generate the same held-out sentences under neutral, happy, and angry settings, including emotionally ambiguous text.
- Have listeners identify the requested emotion without seeing the tag; report a confusion matrix rather than only a pooled quality score.
- Check that the voice remains the same person, the words remain correct, and tags are never spoken aloud.
- Test transitions and long paragraphs, including boundaries between browser-generated chunks. Emotion must not reset merely because synthesis is chunked.
- Check tags on laptop and phone backends after quantization; evaluate the shipped weights, not only the full-precision teacher.
- Measure naturalness and appropriateness. Happy need not mean exaggerated laughter; angry need not mean shouting.
- Treat unsupported events, unknown tags, adjacent tags, escaped brackets, and cancellation/new-request state as explicit frontend/parser cases when implementation begins.

## Primary references

[ElevenLabs' prompting guide](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices) documents bracketed emotion/delivery tags and nonverbal events. It is a behavior reference, not evidence that Oddmouth already supports them.

[Qwen3-TTS's official examples](https://github.com/QwenLM/Qwen3-TTS) demonstrate instruction-conditioned custom voices, including angry/happy directions. Those large models are research/teacher candidates, not a demonstrated sub-50M solution. Their custom-voice and voice-cloning APIs have different conditioning interfaces; do not assume an arbitrary cloned speaker supports the identical instruction path.

[Expresso's official dataset page](https://speechbot.github.io/expresso/) provides expressive style examples and improvised dialogue. Its multi-speaker scope and CC BY-NC license mean it is a reference for expression coverage, not the selected unrestricted single-voice source.
