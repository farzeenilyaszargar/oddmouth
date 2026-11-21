export type MouthPose = 'smile' | 'closed' | 'teeth' | 'open' | 'wide' | 'round' | 'pucker' | 'bite';
export type MouthCue = { start: number; end: number; value: string };

// Rhubarb's sound groups, mapped to this character's original vector artwork.
const poses: Record<string, MouthPose> = {
  A: 'closed', B: 'teeth', C: 'open', D: 'wide', E: 'round',
  F: 'pucker', G: 'bite', H: 'open', X: 'smile',
};

export function mouthPoseAt(cues: readonly MouthCue[], seconds: number): MouthPose {
  if (!Number.isFinite(seconds) || seconds < 0) return 'smile';
  let low = 0;
  let high = cues.length - 1;
  while (low <= high) {
    const middle = (low + high) >>> 1;
    const cue = cues[middle];
    if (seconds < cue.start) high = middle - 1;
    else if (seconds >= cue.end) low = middle + 1;
    else return poses[cue.value] ?? 'smile';
  }
  return 'smile';
}
