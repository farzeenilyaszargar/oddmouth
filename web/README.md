# Oddmouth web

A minimal black-and-white, single-screen Next.js App Router frontend for Oddmouth. Tagline: **Small model. Big mouth.**

## Develop

```sh
cd web
npm ci
npm run dev
```

Open http://localhost:3000. For production, run `npm run build`; the static site is exported to `out/` following [Next.js static export guidance](https://nextjs.org/docs/app/guides/static-exports). `npm run typecheck` checks TypeScript.

## Demo behavior

- Editable text, a 1,000-character input limit, character count, and reset.
- A bundled five-second WAV, play/pause, seeking, replay, and download.
- A vector face based on the supplied logo reference, with discrete mouth poses driven by audio playback time. Pausing freezes the pose, seeking changes it, and reset returns the smile. These expressions are illustrative, not phoneme-aligned enunciation guidance.
- Reduced-motion preferences show the static logo instead.
- An accessible native About dialog, dismissible with its close button, Escape, or the backdrop.
- A 100svh shell keeps the navbar and footer in one viewport. The central workspace can scroll internally on unusually short screens or at high text zoom.
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

## Model integration

Connect an actual inference pipeline before presenting custom speech generation. Keep the current demo label until the player receives audio synthesized from the submitted text. Model weights, bulk audio, and checkpoints belong in artifact storage, not this frontend or ordinary Git.
