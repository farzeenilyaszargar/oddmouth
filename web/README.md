# Oddmouth web

A single-page Next.js demo for Oddmouth. It is **not yet connected to the model**: the Generate button plays a bundled, prerecorded sample.

```sh
cd web
npm ci
npm run dev        # http://localhost:3000
npm run build      # static export to out/
npm test           # lip-sync cue tests
npm run typecheck
```

## Local training review

From the repository root, export a saved run with
`uv run python scripts/export_review.py --stage vocoder --run runs/vocoder`.
Use `--stage acoustic --run runs/acoustic` after saving an acoustic checkpoint.
In a second terminal under `web/`, run `node scripts/review-server.mjs` alongside
`npm run dev`, then open [Training review](http://localhost:3000/training/).
Choose a run and play each reference beside its model output. Refresh after
exporting another checkpoint. Review files live in ignored `outputs/` and are
served only through the local development site.

## What's here

- A text editor (1,000-character UI limit), with player controls and WAV download for the demo sample.
- An animated face whose mouth follows the audio, using cues in `demo/lip-sync.json` generated with [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync). Regenerate them with `npm run lip-sync -- /path/to/rhubarb`.
- Locally bundled fonts (Baloo 2, Nunito), with no external requests or analytics.
- Search and share metadata. Set `SITE_URL` before a production build; without it, pages are `noindex`.

## Demo audio

`public/audio/oddmouth-demo.wav` was made with the macOS "Samantha" voice. It is **not Oddmouth output**:

```sh
say -v Samantha -r 150 -o /tmp/demo.aiff 'Some words are better out loud. Give your ideas a voice with Oddmouth.'
ffmpeg -y -i /tmp/demo.aiff -af apad -t 5 -ar 22050 -ac 1 public/audio/oddmouth-demo.wav
```

Replace it with real Oddmouth output once a model is trained and exported to ONNX.
