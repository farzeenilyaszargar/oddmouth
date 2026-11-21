# Oddmouth: selected voice and training preparation

Updated 21 November 2026. The user listened to Dewayne Noel and selected him as the desired voice. **Listening approval is recorded; a licence for the intended recordings, synthetic voice, and model distribution has not been established.**

## Current state

- Selected speaker: Dewayne Noel / Dry Creek Wrangler.
- Intended output: expressive narration and conversational YouTube voiceovers, including happy/angry controls.
- Complete deployed model: at most 50M learned parameters, including the audio decoder.
- Available metadata: 209 podcast episodes with 87:03:34 listed programme duration. Clean target-speaker hours remain unmeasured.
- Updated user constraint: download only if necessary, in chunks no larger than 1,000,000,000 bytes. Planning needs no voice audio; no audio acquisition or training has started. See [the Mac training system](MAC_TRAINING_SYSTEM.md) for architecture, bounded working storage, and training stages.
- A search of official sources and public reports did not verify the user's report that Dewayne has died. Do not record that as an established fact.

## Ownership question

Death does not itself make a creator's recordings unowned. U.S. copyright law permits copyright to pass through a will or inheritance; modern works commonly remain protected beyond the author's death. These general rules do not determine ownership or whether a particular training use is lawful in every jurisdiction. No conclusion that this corpus is public domain or that its rights are abandoned is supported.

Sources: [Copyright ownership and transfer, 17 USC 201(d)(1)](https://www.copyright.gov/title17/92chap2.html), [Copyright Office duration FAQ](https://www.copyright.gov/help/faq/faq-duration.html). The creator's [current website](https://drycreekwranglers.com/) and our saved podcast metadata carry copyright notices. No permissive training grant was located.

The intended product makes the scope important: browser inference requires distributing downloadable model weights, rather than only privately generating recordings. Confirm an appropriate basis for the recordings, training, commercial generated audio, identity use, and weight redistribution. Keep the public repository's code licence distinct from any resulting voice-model licence.

A local, **unsent** enquiry is in `VOICE_PERMISSION_REQUEST.md`. The [official contact page](https://drycreekwranglers.com/contact-us) publishes the contact address. No one has been contacted on the user's behalf.

## Training experiment once the source and acquisition location are settled

1. Choose a small pilot from original-channel solo episodes spanning different sessions and delivery styles. Avoid guest appearances and third-party motivational edits. Episode titles cannot determine their audio quality or emotion labels.
2. Measure usable speech after removing ads, overlap, music, clipping, long silence, duplicated material, and other speakers. Keep episode IDs and provenance; split by whole episode/session. Establish whether more than 50 hours remain for training after holdouts.
3. Transcribe and align the retained speech, then review errors and audible emotion labels. Preserve conversational pauses and emphasis. Mark uncertainty rather than forcing every clip into neutral/happy/angry.
4. Validate trainability and browser export for a compact pretrained candidate before a large run. Start with a fixed speaker identity; count the actual complete inference graph before approving the architecture.
5. Establish a neutral conversational baseline, then train explicit happy/angry conditioning on demonstrated performances. Measure whether the style changes without changing speaker identity or text. Do not infer angry speech merely from an episode discussing anger.
6. Evaluate on the same texts across emotions, plus long-form narration. Check recognition accuracy, listener-rated emotion, identity consistency, naturalness, and browser latency/memory after quantization.

This plan does not promise that the podcast contains all required emotions, that a direct small-model adaptation recipe is available, or that 50M achieves ElevenLabs parity. Those are empirical questions for the pilot.
