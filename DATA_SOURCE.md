# Oddmouth voice-data search: expressive creator delivery

Source research checked on 21 November 2026. **Source identification only: no audio dataset has been downloaded.**

## Current decision

**The user rejected the audiobook delivery after listening. John Van Stan / Hi-Fi TTS is no longer the recommended target voice.** It meets the published hours requirement but misses the desired expressive, conversational YouTube presentation style.

The target is a deep male creator voice: engaged explanation, storytelling, rhetorical questions, emphasis, reactions, and natural changes in pace. Audio cleanliness and quantity alone are insufficient. No replacement is approved yet, and no source meeting all requirements has been verified.

## Leading source to audition: Chris Fisher / LINUX Unplugged

- [Host profile](https://www.jupiterbroadcasting.com/hosts/chris/)
- [Example episode: Chris' Data Crisis](https://www.jupiterbroadcasting.com/show/linux-unplugged/355/)
- [Streaming sample from 8:02, the “BTRFS Backfire” story section](https://www.youtube.com/watch?v=5wjkKPhBQkU&t=482s)
- [Publisher's license statement](https://www.jupiterbroadcasting.com/membership/): shows licensed under CC BY-SA 4.0.

This is a **raw podcast source candidate**, not an existing single-speaker TTS dataset. It provides spontaneous discussion and personal stories to audition against the requested performance style. The example episode lists Chris alongside other hosts and a guest. Its complete duration must not be counted as Chris's usable speech.

The archive provides a plausible route to substantial material, but **50 clean hours of Chris alone have not been measured or verified**. The RSS endpoint returned 403 during this check, so no feed-duration total is claimed. Timbre and suitability for an older/grandpa character also need listening approval.

If selected later, preparation would identify one speaker across episodes, remove cohosts, overlapping speech, music, ads, guest clips, and noisy passages, transcribe and align the retained speech, and measure usable hours. Split by episode/session. This preserves a single target voice from one publishing source even though the raw episodes contain multiple people. If the user requires recordings that contain only one person from the outset, this source does not meet that stricter requirement.

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) includes attribution and ShareAlike conditions and identifies possible additional rights. The publisher's show license is not evidence of a separate synthetic-voice authorization from Chris. Such authorization and the intended model-distribution terms have not been established. No one was contacted.

## Other sources checked

| Source | Why it is relevant | Why it is not the selected replacement |
|---|---|---|
| [Expresso](https://speechbot.github.io/expresso/) | Professional expressive speech and improvised dialogues, with examples of happy, sarcastic, laughing, and other delivery styles | Four speakers; its duration table totals 45.9 hours across them, not >50 hours for one person; CC BY-NC 4.0. Useful to audition delivery, not the default unrestricted training source. |
| [RyanSpeech paper](https://arxiv.org/abs/2106.08468) | One male professional actor, conversational text, over 10 hours | Below the requested hours. The [publisher's current access terms](https://mohammadmahoor.com/pages/databases/ryanspeech/forms/ryanspeech/) state CC BY-NC-ND 4.0, despite older descriptions calling it non-restrictive. Not assumed commercially usable. |
| [Emilia](https://huggingface.co/datasets/amphion/Emilia-Dataset/blob/fc71e07/README.md) | In-the-wild speech rather than only audiobooks | Large total hours do not prove >50 hours for one suitable speaker. The original release states noncommercial use and that original audio copyright remains with owners. Not an unrestricted single-voice solution. |

## Selection rule going forward

Choose performance style first, then verify speaker consistency, usable hours, sound quality, transcripts, and rights. Prefer suitable expressive data over filling an hours target with dull delivery. The user's preference remains above 50 hours; no smaller dataset is silently substituted.

The user also requires explicit `[happy]` and `[angry]` controls. A candidate must therefore be assessed for emotion coverage in the same target voice, not just overall conversational quality. See `EXPRESSION_CONTROLS.md`. No current candidate has passed that coverage check.

Training on neutral audiobooks may teach a small model to read competently without teaching the intended presentation style. A pretrained model's expressive ability can help adaptation, but a speed/pitch control or a style label alone does not establish convincing expressive generation. Any teacher-assisted style expansion must be tested rather than assumed to fix the mismatch.

## Historical candidate: Hi-Fi TTS (rejected for delivery)

The **John Van Stan subset of Hi-Fi TTS**, speaker ID **9017**, was the first candidate. Its source details remain below for provenance, not as a current recommendation.

| Field | Published information |
|---|---|
| Corpus | Hi-Fi Multi-Speaker English TTS Dataset, OpenSLR 109 |
| Publisher | NVIDIA |
| Selected speaker | John Van Stan, ID 9017 |
| Duration | **58.0 hours**, all in the clean subset |
| Sampling rate | 44.1 kHz |
| Supervision | Segmented speech with corresponding transcripts |
| Dataset license | CC BY 4.0 |

The duration and speaker identity are reported in **Table 2, page 3** of the [dataset paper](https://www.isca-archive.org/interspeech_2021/bakhturina21_interspeech.pdf). This is a published duration, not a local audit of usable training hours. Filtering and evaluation holdouts will reduce the eventual training set.

## Links

- [Official dataset and license listing](https://openslr.org/109/)
- [Dataset paper](https://www.isca-archive.org/interspeech_2021/bakhturina21_interspeech.pdf)
- [Speaker's LibriVox profile](https://librivox.org/reader/9017)
- [Community Hugging Face mirror](https://huggingface.co/datasets/MikhailT/hifi-tts)

The official download contains multiple speakers. A future acquisition must select **only speaker 9017 / clean**. The mirror is a repackaging of the same corpus, not an additional voice source. Its observed revision is recorded in `configs/data_source.json` for reproducibility. No mirror audio was downloaded or compared with the official archive.

## Listen before choosing

- [Streaming preview on the official LibriVox Audiobooks YouTube channel](https://www.youtube.com/watch?v=6BUH8tIueh8)
- [Original book page with chapter players and John Van Stan attribution](https://librivox.org/thus-spake-zarathustra-by-friedrich-nietzsche-2/)
- [Internet Archive streaming player](https://archive.org/details/zarathustra_2010_librivox)

The sample is **original human narration**, not an Oddmouth model output. It lets the user judge the voice character; it does not establish how a trained model will sound. The browser preview is a stream; no audio file is saved to this repository. The YouTube preview was started successfully; direct MP3 navigation was blocked by the in-app browser.

## Why the historical candidate was considered

It satisfies the requested published duration above 50 hours for one male speaker and supplies text/audio pairs intended for TTS. The user's listening feedback establishes that its read-aloud delivery is not the intended Oddmouth voice.

The [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/) permit reuse with attribution and other conditions, while identifying that other rights can still apply. The corpus license alone does not establish an explicit synthetic-voice permission from this speaker. No such permission was verified during this source lookup.

## Project constraints retained

- Target a complete deployed neural pipeline of **50M parameters or fewer**, including its audio decoder. No model count is claimed yet.
- Do not download the voice dataset locally unless the user later requests it.
- Store source documentation and project changes in the Oddmouth GitHub repository.
- Before future training, measure available hours after filtering and holdouts. Do not substitute the 58-hour headline for a verified training manifest.
