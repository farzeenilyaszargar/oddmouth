'use client';

import { useEffect, useState, type RefObject } from 'react';
import Mouth from './mouth';
import { mouthPoseAt, type MouthCue, type MouthPose } from './lib/lip-sync';

type Props = { audio: RefObject<HTMLAudioElement | null>; cues: readonly MouthCue[]; playing: boolean; time: number; duration: number; editing: boolean; sourceRate?: number };

export default function SpeakingMouth({ audio, cues, playing, time, duration, editing, sourceRate = 1 }: Props) {
  const [framePose, setFramePose] = useState<MouthPose>('smile');
  const resting = time === 0 || time >= duration;
  const idle = !playing && resting && !editing;

  useEffect(() => {
    if (!playing || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let frame = 0;
    let previous: MouthPose | undefined;
    const tick = () => {
      const pose = mouthPoseAt(cues, (audio.current?.currentTime ?? 0) * sourceRate);
      // Read the media clock each frame, but render only at a cue boundary.
      if (pose !== previous) { setFramePose(pose); previous = pose; }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [audio, cues, playing, sourceRate]);

  const pose = playing ? framePose : editing && resting ? 'smile' : mouthPoseAt(cues, time * sourceRate);
  return <Mouth pose={pose} playful={idle} trackEyes className="animated-mouth" />;
}
