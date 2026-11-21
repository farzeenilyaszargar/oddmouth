import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { mouthPoseAt } from '../app/lib/lip-sync.ts';

const data = JSON.parse(readFileSync(new URL('../demo/lip-sync.json', import.meta.url), 'utf8'));

test('cue data belongs to the bundled audio, covers it, and contains all sound groups', () => {
  const wav = readFileSync(new URL('../public/audio/oddmouth-demo.wav', import.meta.url));
  assert.equal(createHash('sha256').update(wav).digest('hex'), data.audioSha256);
  assert.equal(data.mouthCues[0].start, 0);
  let end = 0;
  for (const cue of data.mouthCues) {
    assert.equal(cue.start, end, 'no gaps or overlapping sound cues');
    assert.ok(cue.end > cue.start);
    end = cue.end;
  }
  assert.equal(end, data.duration);
  assert.deepEqual([...new Set(data.mouthCues.map(cue => cue.value))].sort(), ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X']);
});

test('speech sounds map to distinct poses at their actual times', () => {
  assert.equal(mouthPoseAt(data.mouthCues, .22), 'closed'); // M in “some”
  assert.equal(mouthPoseAt(data.mouthCues, .31), 'pucker'); // W in “words”
  assert.equal(mouthPoseAt(data.mouthCues, 1.25), 'open'); // L in “loud”
  assert.equal(mouthPoseAt(data.mouthCues, 2.13), 'bite'); // V in “give”
  assert.equal(mouthPoseAt(data.mouthCues, .63), 'wide');
  assert.equal(mouthPoseAt(data.mouthCues, .36), 'round');
});

test('seeking uses the new cue immediately, including exact cue boundaries', () => {
  assert.equal(mouthPoseAt(data.mouthCues, .19), 'closed');
  assert.equal(mouthPoseAt(data.mouthCues, .29), 'pucker');
  assert.equal(mouthPoseAt(data.mouthCues, 2.17), 'pucker');
  assert.equal(mouthPoseAt(data.mouthCues, .04), 'teeth');
});

test('silence, end, reset and invalid times return to rest', () => {
  for (const time of [0, 1.75, 4.5, 5, 20, -1, NaN, Infinity]) {
    assert.equal(mouthPoseAt(data.mouthCues, time), 'smile');
  }
  assert.equal(mouthPoseAt([], 1), 'smile');
});
