import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_AUDIO, originalAudio, outputFrames, wavBytes } from '../app/lib/audio-effects.ts';

test('default settings retain the original sample and edits require rendering', () => {
  assert.equal(originalAudio(DEFAULT_AUDIO), true);
  for (const change of [{ effect: 'radio' }, { speed: 1.5 }, { volume: 0 }, { tone: 2000 }, { background: 'vinyl' }]) {
    assert.equal(originalAudio({ ...DEFAULT_AUDIO, ...change }), false);
  }
});

test('speed changes the rendered duration', () => {
  assert.equal(outputFrames(110250, 1.5), 73500);
  assert.equal(outputFrames(110250, .75), 147000);
});

test('download WAV contains interleaved PCM and clips out-of-range samples safely', () => {
  const left = new Float32Array([-2, 0, 2]);
  const right = new Float32Array([.5, -.5, 0]);
  const bytes = wavBytes({ length: 3, numberOfChannels: 2, sampleRate: 22050, getChannelData: channel => channel ? right : left });
  const view = new DataView(bytes);
  assert.equal(new TextDecoder().decode(bytes.slice(0, 4)), 'RIFF');
  assert.equal(view.getUint16(22, true), 2);
  assert.equal(view.getUint32(24, true), 22050);
  assert.equal(view.getUint32(40, true), 12);
  assert.equal(view.getInt16(44, true), -32768);
  assert.equal(view.getInt16(46, true), 16384);
  assert.equal(view.getInt16(50, true), -16384);
  assert.equal(view.getInt16(52, true), 32767);
});
