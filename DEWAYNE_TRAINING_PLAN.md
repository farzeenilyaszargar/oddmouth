# Oddmouth: selected voice and training preparation

Updated 21 November 2026. The user listened to Dewayne Noel and selected him as the desired voice. **Listening approval is recorded; a licence for the intended recordings, synthetic voice, and model distribution has not been established.**

## Current state

- Selected speaker: Dewayne Noel / Dry Creek Wrangler.
- Intended output: naturally engaging narration and conversational YouTube voiceovers, with no explicit emotion controls.
- Complete deployed model: at most 50M learned parameters, including the audio decoder.
- Available metadata: 209 podcast episodes with 87:03:34 listed programme duration. Clean target-speaker hours remain unmeasured.
- Updated user constraint: download only if necessary, in chunks no larger than 1,000,000,000 bytes. Planning needs no voice audio; no audio acquisition or training has started. See [the Mac training system](MAC_TRAINING_SYSTEM.md) for architecture, bounded working storage, and training stages.
- A search of official sources and public reports did not verify the user's report that Dewayne has died. Do not record that as an established fact.

## Ownership question

Death does not itself make a creator's recordings unowned. U.S. copyright law permits copyright to pass through a will or inheritance; modern works commonly remain protected beyond the author's death. These general rules do not determine ownership or whether a particular training use is lawful in every jurisdiction. No conclusion that this corpus is public domain or that its rights are abandoned is supported.

Sources: [Copyright ownership and transfer, 17 USC 201(d)(1)](https://www.copyright.gov/title17/92chap2.html), [Copyright Office duration FAQ](https://www.copyright.gov/help/faq/faq-duration.html). The creator's [current website](https://drycreekwranglers.com/) and our saved podcast metadata carry copyright notices. No permissive training grant was located.

The intended product makes the scope important: browser inference requires distributing downloadable model weights, rather than only privately generating recordings. Confirm an appropriate basis for the recordings, training, commercial generated audio, identity use, and weight redistribution. Keep the public repository's code licence distinct from any resulting voice-model licence.

A local, **unsent** enquiry is in `VOICE_PERMISSION_REQUEST.md`. The [official contact page](https://drycreekwranglers.com/contact-us) publishes the contact address. No one has been contacted on the user's behalf.

## Training from scratch on one speaker

1. Select original-channel solo recordings across sessions. Remove music, ads, overlap, other voices, duplication and damaged audio. Measure clean usable hours rather than relying on feed runtime.
2. Correct transcripts and word boundaries; preserve natural pauses and emphasis. Split by whole session before training. No emotion labels are needed.
3. Build a compact text encoder, duration/prosody predictors and flow acoustic model with random weights. Train only on this speaker's pairs; learn alignment from training data or use checked offline boundaries.
4. Separately initialize and train a waveform generator and training-only discriminators from scratch on the same speaker. No pretrained vocoder is substituted.
5. Integrate the two trained components, evaluate unseen text and natural narration, then validate browser export and selective quantization. No pretrained speaking weights, other-speaker pretraining, synthetic teacher speech or distillation are part of the plan.

See [the Mac training system](MAC_TRAINING_SYSTEM.md) for losses, bounded cache rotation, separate phase settings, resumption and measurement gates. The complete model remains below 50M parameters including its vocoder. One-speaker scratch training may require substantial iteration and compute; no ElevenLabs parity or completion time is established.
