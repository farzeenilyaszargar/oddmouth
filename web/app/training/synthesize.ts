import { env, InferenceSession, Tensor } from 'onnxruntime-web/wasm';
import { phonemize } from 'phonemizer';

type Model = {
  sampleRate: number;
  symbols: Record<string, number>;
  blank: number;
  unknown: number;
  steps: number;
  melMean: number[];
  melStd: number[];
};

type Sessions = [InferenceSession, InferenceSession, InferenceSession];
let active: { id: string; sessions: Sessions; config: Model } | undefined;

async function load(id: string) {
  if (active?.id === id) return active;
  if (active) {
    await Promise.all(active.sessions.map(session => session.release()));
    active = undefined;
  }
  env.wasm.numThreads = 1;
  env.wasm.wasmPaths = new URL('/training-files/runtime/', window.location.origin).href;
  const base = `/training-files/${encodeURIComponent(id)}/model/`;
  const response = await fetch(base + 'model.json');
  if (!response.ok) throw new Error('This checkpoint has no browser export.');
  const config: Model = await response.json();
  const sessions: InferenceSession[] = [];
  try {
    for (const file of ['text', 'flow', 'vocoder']) {
      const graph = await fetch(base + file + '.onnx', { cache: 'no-cache' });
      if (!graph.ok) throw new Error('Couldn’t load the voice model.');
      sessions.push(await InferenceSession.create(await graph.arrayBuffer(), {
        executionProviders: ['wasm'],
      }));
    }
  } catch (error) {
    await Promise.all(sessions.map(session => session.release()));
    throw error;
  }
  active = { id, config, sessions: [sessions[0], sessions[1], sessions[2]] };
  return active;
}

async function tokenize(text: string, config: Model) {
  const pieces = text.replace(/\s+/g, ' ').trim().split(/([;:,.!?…—]+)/);
  const ipa = (await Promise.all(pieces.map(async (piece, index) => {
    if (index % 2 || !piece.trim()) return piece;
    const phones = (await phonemize(piece.trim(), 'en-us')).join(' ');
    return piece.replace(piece.trim(), () => phones);
  }))).join('');
  const ids = [config.blank];
  for (const symbol of ipa) ids.push(config.symbols[symbol] ?? config.unknown, config.blank);
  if (ids.length < 3) throw new Error('Enter a few words to speak.');
  if (ids.length > 240) throw new Error('Use a shorter phrase for the preview.');
  return new Tensor('int64', BigInt64Array.from(ids, BigInt), [1, ids.length]);
}

function seededNoise(length: number) {
  let seed = 2026;
  const uniform = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return (seed + 1) / 4294967297;
  };
  return Float32Array.from({ length }, () =>
    Math.sqrt(-2 * Math.log(uniform())) * Math.cos(2 * Math.PI * uniform()) * 0.667);
}

function repeatRows(values: Float32Array, width: number, durations: number[], frames: number) {
  const repeated = new Float32Array(frames * width);
  let offset = 0;
  for (const [token, duration] of durations.entries()) {
    const row = values.subarray(token * width, (token + 1) * width);
    for (let i = 0; i < duration; i++, offset += width) repeated.set(row, offset);
  }
  return new Tensor('float32', repeated, [1, frames, width]);
}

function wav(samples: Float32Array, sampleRate: number) {
  const bytes = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(bytes);
  for (const [offset, label] of [[0, 'RIFF'], [8, 'WAVEfmt '], [36, 'data']] as const) {
    for (let i = 0; i < label.length; i++) view.setUint8(offset + i, label.charCodeAt(i));
  }
  view.setUint32(4, bytes.byteLength - 8, true);
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    if (!Number.isFinite(samples[i])) throw new Error('The checkpoint produced invalid audio.');
    view.setInt16(44 + i * 2, Math.round(Math.max(-1, Math.min(samples[i], 1)) * 32767), true);
  }
  return new Blob([bytes], { type: 'audio/wav' });
}

export async function synthesize(id: string, text: string, onReady: () => void) {
  const { config, sessions: [encoder, decoder, vocoder] } = await load(id);
  onReady();
  const encoded = await encoder.run({ tokens: await tokenize(text, config) });
  const durations = Array.from(encoded.duration.data as Float32Array, value => Math.max(1, Math.ceil(Math.exp(value))));
  const frames = durations.reduce((sum, n) => sum + n, 0);
  if (!Number.isFinite(frames) || frames > 600) throw new Error('The predicted audio is too long. Try fewer words.');
  const bins = config.melMean.length;
  const prior = repeatRows(encoded.prior.data as Float32Array, bins, durations, frames);
  const condition = repeatRows(encoded.condition.data as Float32Array, encoded.condition.dims[2], durations, frames);
  const noise = seededNoise(frames * bins);
  for (let i = 0; i < config.steps; i++) {
    const { velocity } = await decoder.run({
      noise: new Tensor('float32', noise, [1, frames, bins]), prior, condition,
      time: new Tensor('float32', [i / config.steps], [1]),
    });
    const delta = velocity.data as Float32Array;
    for (let j = 0; j < noise.length; j++) noise[j] += delta[j] / config.steps;
  }
  const mel = new Float32Array(frames * bins);
  for (let c = 0; c < bins; c++) {
    for (let t = 0; t < frames; t++) mel[c * frames + t] = noise[t * bins + c] * config.melStd[c] + config.melMean[c];
  }
  const { wave } = await vocoder.run({ mel: new Tensor('float32', mel, [1, bins, frames]) });
  return wav(wave.data as Float32Array, config.sampleRate);
}
