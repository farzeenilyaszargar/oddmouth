# Oddmouth web

A minimal black-and-white, single-screen Next.js App Router frontend for Oddmouth.

## Develop

```sh
cd web
npm ci
npm run dev
```

Open http://localhost:3000. For production, run `npm run build`; the static site is exported to `out/` following [Next.js static export guidance](https://nextjs.org/docs/app/guides/static-exports). `npm run typecheck` checks TypeScript.

## Demo behavior

- Editable text, a 1,000-character input limit, character count, and reset.
- A black Generate demo button restarts and plays the prerecorded sample. It does not synthesize the entered text and is disabled when the input is blank.
- A compact character and one descriptive introduction paragraph keep the editor near the top of the page.
- A bundled five-second WAV, play/pause, seeking, replay, and download.
- A vector face with eight sound-specific mouth poses, driven by audio-aligned cues extracted from the recording with Rhubarb Lip Sync. Pausing freezes the pose, seeking selects the matching sound, and silence/reset returns the smile. Alignment is automatic and approximate, not validated pronunciation instruction.
- The eyes follow the pointer across the page, including during speech. The idle animation is a small grin tilt and a quick wink, followed by a quiet pause. It uses a smooth eight-second CSS loop, with no protruding mouth artwork or timed pose swaps. Focusing the editor stops idle expressions, and speech or paused speech cues take priority. Pointer listeners and playback animation frames are cleaned up on unmount; the idle animation needs no JavaScript timer.
- Reduced-motion preferences show the static logo instead.
- An accessible native About dialog, dismissible with its close button, Escape, or the backdrop.
- A 100svh shell keeps the navbar and workspace in one viewport. The central workspace can scroll internally on unusually short screens or at high text zoom.
- Editing the text does not synthesize audio. The sample is always identified as a prerecorded demo. No model, inference endpoint, analytics, or external font requests are included.
- Text stays only in page memory and is cleared on refresh. The 1,000-character limit is a UI placeholder, not a model constraint.

## Sample provenance

`public/audio/oddmouth-demo.wav` is a small UI fixture generated on macOS with the system Samantha voice, not the Oddmouth model or a training-data sample. It says:

> Some words are better out loud. Give your ideas a voice with Oddmouth.

Reproduce it on macOS with Samantha installed and FFmpeg available:

```sh
say -v Samantha -r 150 -o /tmp/oddmouth-demo.aiff 'Some words are better out loud. Give your ideas a voice with Oddmouth.'
ffmpeg -y -i /tmp/oddmouth-demo.aiff -af apad -t 5 -ar 22050 -ac 1 public/audio/oddmouth-demo.wav
```

Output: mono PCM WAV, 22,050 Hz, exactly five seconds including trailing silence. This fixture does not establish Oddmouth voice quality, model size, or inference performance. Replace it with a licensed final voice audition before launch.

## Speech-driven mouth animation

`demo/lip-sync.json` contains 38 timestamped mouth cues extracted from the actual demo WAV with [Rhubarb Lip Sync 1.14.0](https://github.com/DanielSWolf/rhubarb-lip-sync/releases/tag/v1.14.0), using its English PocketSphinx recognizer and the exact transcript in `demo/transcript.txt`. The file records the audio SHA-256 so changed recordings cannot silently reuse old timings.

The A-H/X cues drive eight vector expressions: closed lips, clenched teeth, open, wide open, rounded, puckered, teeth on the lip, and resting smile. H uses the open-mouth drawing. The animation reads the media clock on each animation frame and renders only when the pose changes. It does not use a repeating animation timer. Reduced-motion preferences retain the static face.

To regenerate, download and extract the official Rhubarb release outside the repository, then run from `web/`:

```sh
npm run lip-sync -- /absolute/path/to/rhubarb
npm test
```

The generator reads only the bundled fixture and transcript, strips machine-specific paths from its output, and records the generator version. Rhubarb binaries and recognizer models stay outside Git. The runtime only needs the small JSON cue file, with no speech recognition downloads. Tests check the audio fingerprint, continuous cue coverage, sound mapping, seeking boundaries, and rest intervals.

## Model integration

Connect an actual inference pipeline before presenting custom speech generation. Keep the current demo label until the player receives audio synthesized from the submitted text. New generated recordings must include their own timing cues (from inference phoneme timing or a separate alignment step); the current cues apply only to the demo WAV. Model weights, bulk audio, and checkpoints belong in artifact storage, not this frontend or ordinary Git.

## Search and sharing

The page includes a descriptive title, description, Open Graph and Twitter cards, a 1200 x 630 share image, an explicit icon, and WebSite structured data. The copy describes the current demo rather than claiming that custom generation is available.

Set `SITE_URL` to the final public origin before the production build. This adds the canonical URL and a one-page sitemap and enables crawling. For private staging, set `SITE_INDEXABLE=false`. With no configured public URL, localhost and preview builds use `noindex`, block crawling in `robots.txt`, and return an empty sitemap. Private hosting must also be made public before search engines can access it. Metadata cannot guarantee search rankings.

The share image source is `public/social-card.svg`; its PNG is used for link previews. To regenerate the PNG using the installed Sharp dependency, run from `web/`:

```sh
node --input-type=module -e "import sharp from 'sharp'; await sharp('public/social-card.svg').png().toFile('public/social-card.png')"
```
