# Oddmouth's first voice-data candidate

Source research checked on 21 November 2026. **Source identification only: no audio dataset has been downloaded.**

## Recommended source

Use the **John Van Stan subset of Hi-Fi TTS**, speaker ID **9017**. This provides a single male English narrator from one corpus, rather than a mixture of speakers.

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

## Why this is the first candidate

It satisfies the requested published duration above 50 hours for one male speaker and supplies text/audio pairs intended for TTS. Its read-aloud material is a better immediate fit for narration than spontaneous conversation. Depth, warmth, and similarity to the desired grandpa style remain subject to the user's listening judgment.

The [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/) permit reuse with attribution and other conditions, while identifying that other rights can still apply. The corpus license alone does not establish an explicit synthetic-voice permission from this speaker. No such permission was verified during this source lookup.

## Project constraints retained

- Target a complete deployed neural pipeline of **50M parameters or fewer**, including its audio decoder. No model count is claimed yet.
- Do not download the voice dataset locally unless the user later requests it.
- Store source documentation and project changes in the Oddmouth GitHub repository.
- Before future training, measure available hours after filtering and holdouts. Do not substitute the 58-hour headline for a verified training manifest.
