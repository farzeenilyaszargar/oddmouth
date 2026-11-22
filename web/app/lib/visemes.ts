import type { MouthCue } from './lip-sync';

// Map espeak IPA symbols to Rhubarb's mouth groups (A-H, X), so generated
// speech can drive the same artwork as the bundled demo:
// A closed (p b m), B teeth (most consonants, i), C open, D wide (a),
// E slightly round (ɔ ɜ ɹ), F pucker (u o w), G bite (f v), H tongue (l), X rest.
const GROUPS: Record<string, string> = {};
const assign = (group: string, symbols: string) => { for (const s of symbols) GROUPS[s] = group; };
assign('A', 'pbm');
assign('B', 'tdsznkgŋhjθðʃʒʤʧʔɾçxiɪyʏ');
assign('C', 'eɛæʌəɐɨ');
assign('D', 'aɑɒ');
assign('E', 'ɔɜɝɚɹr');
assign('F', 'uʊoɵwʍ');
assign('G', 'fv');
assign('H', 'lɫ');
assign('X', ',.!?;:…—-()"\'');

/** Mouth group for one IPA symbol; null means "keep the previous shape". */
export function mouthGroup(symbol: string): string | null {
  return GROUPS[symbol] ?? null;
}

/**
 * Turn per-symbol frame counts into mouth cues in seconds.
 * symbols[i] is the text symbol for token i (null for the model's blank tokens),
 * frames[i] is how many spectrogram frames the model gave that token.
 */
export function cuesFromDurations(symbols: readonly (string | null)[], frames: readonly number[],
  secondsPerFrame: number, offset = 0): MouthCue[] {
  const cues: MouthCue[] = [];
  let time = offset;
  let current = 'X';
  for (let i = 0; i < frames.length; i++) {
    const symbol = symbols[i];
    if (symbol !== null && symbol !== undefined) {
      // A space between words keeps the mouth moving; only punctuation rests it.
      current = mouthGroup(symbol) ?? current;
    }
    const end = time + frames[i] * secondsPerFrame;
    const last = cues[cues.length - 1];
    if (last && last.value === current) last.end = end;
    else if (end > time) cues.push({ start: time, end, value: current });
    time = end;
  }
  return cues;
}
