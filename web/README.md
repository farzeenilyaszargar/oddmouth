# Oddmouth web

A single-page Next.js demo for Oddmouth. On the local development site, **Generate speaks with the newest exported training checkpoint**, in the browser, and the mouth follows the model's predicted timing for each sound. The public build has no model yet, so Generate plays a bundled, prerecorded sample.

```sh
cd web
npm ci
npm run dev        # http://localhost:3000
npm run build      # static export to out/
npm test           # lip-sync cue tests
npm run typecheck
```

## Try saved checkpoints locally

Run these commands from the repository root after saving both checkpoints:

```sh
uv sync --extra browser
uv run python scripts/export_review.py --stage acoustic --run runs/acoustic
uv run --extra browser python scripts/export_browser.py --review-id acoustic-acoustic-0000042
```

Use the review ID printed by the first script. In two terminals under `web/`,
run `node scripts/review-server.mjs` and `npm run dev`. Open
[Test the voice](http://localhost:3000/training/), choose a checkpoint, and
generate a short sentence. Refresh after exporting a new checkpoint. The
browser uses the same seed for repeatable comparisons. Model files stay in
ignored `outputs/` and are excluded from the production build.

## What's here

- A text editor (1,000-character UI limit), with player controls and WAV download for the demo sample.
- An animated face whose mouth follows the audio. For generated speech, each phoneme's predicted duration maps to a mouth shape (`app/lib/visemes.ts`). For the bundled sample, cues in `demo/lip-sync.json` come from [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync); regenerate them with `npm run lip-sync -- /path/to/rhubarb`.
- Long text is split into short phrases (`app/lib/phrases.ts`), because the model was trained on clips of about 8 words.
- Locally bundled fonts (Baloo 2, Nunito), with no external requests or analytics.
- Search and share metadata. Set `SITE_URL` before a production build; without it, pages are `noindex`.

## Demo audio

`public/audio/oddmouth-demo.wav` was made with the macOS "Samantha" voice. It is **not Oddmouth output**:

```sh
say -v Samantha -r 150 -o /tmp/demo.aiff 'Some words are better out loud. Give your ideas a voice with Oddmouth.'
ffmpeg -y -i /tmp/demo.aiff -af apad -t 5 -ar 22050 -ac 1 public/audio/oddmouth-demo.wav
```

Replace it with real Oddmouth output once a model is trained and exported to ONNX.

## Audio editing

More opens a compact settings panel, hidden by default. It offers Natural, Radio, and Telephone voice filters, speed, volume, a low-pass filter, and synthesized rain or vinyl background textures with an adjustable level. Closing the panel keeps the settings.

Edits run locally through `OfflineAudioContext`, with short input debouncing. Playback and download use the same rendered PCM WAV. Speed changes both duration and pitch; the mouth animation maps the edited playback position back to the source audio timing. Returning to the default settings uses the original fixture. Blob URLs are released when replaced or unmounted. No external sound files, audio uploads, or new model inference are involved.
