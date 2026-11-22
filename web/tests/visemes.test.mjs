import test from 'node:test';
import assert from 'node:assert/strict';
import { cuesFromDurations, mouthGroup } from '../app/lib/visemes.ts';
import { phrases } from '../app/lib/phrases.ts';

test('IPA symbols map to mouth groups', () => {
  assert.equal(mouthGroup('m'), 'A');
  assert.equal(mouthGroup('ɑ'), 'D');
  assert.equal(mouthGroup('u'), 'F');
  assert.equal(mouthGroup('f'), 'G');
  assert.equal(mouthGroup('l'), 'H');
  assert.equal(mouthGroup('.'), 'X');
  assert.equal(mouthGroup('ˈ'), null);
});

test('cues follow model durations without gaps and merge repeats', () => {
  // blank, h, blank, ˈ, blank, ɑ, blank, ., blank  ("hah.")
  const symbols = [null, 'h', null, 'ˈ', null, 'ɑ', null, '.', null];
  const frames = [1, 2, 1, 1, 1, 4, 1, 3, 1];
  const cues = cuesFromDurations(symbols, frames, 0.01, 1);
  assert.deepEqual(cues.map(c => c.value), ['X', 'B', 'D', 'X']);
  assert.equal(cues[0].start, 1);
  for (let i = 1; i < cues.length; i++) assert.equal(cues[i].start, cues[i - 1].end);
  assert.ok(Math.abs(cues.at(-1).end - 1.15) < 1e-9);
});

test('long text splits into short phrases with pauses', () => {
  const parts = phrases('Hey everyone. ' + Array(30).fill('word').join(' ') + ', done!');
  assert.equal(parts[0].text, 'Hey everyone.');
  assert.ok(parts.every(part => part.text.split(' ').length <= 14));
  assert.equal(parts.at(-1).pause, 0.3);
  assert.deepEqual(phrases('  ... '), []);
});
