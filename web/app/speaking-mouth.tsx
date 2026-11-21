'use client';

import { useEffect, useState, type RefObject } from 'react';
import Mouth from './mouth';
import { mouthPoseAt, type MouthPose } from './lib/lip-sync';
import animation from '../demo/lip-sync.json';

type Props = { audio: RefObject<HTMLAudioElement | null>; playing: boolean; time: number; duration: number; editing: boolean };

export default function SpeakingMouth({ audio, playing, time, duration, editing }: Props) {
  const [framePose, setFramePose] = useState<MouthPose>('smile');
  const resting = time === 0 || time >= duration;
  const idle = !playing && resting && !editing;

  useEffect(() => {
    if (!playing || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let frame = 0;
    let previous: MouthPose | undefined;
    const tick = () => {
      const pose = mouthPoseAt(animation.mouthCues, audio.current?.currentTime ?? 0);
      // Read the media clock each frame, but render only at a cue boundary.
      if (pose !== previous) { setFramePose(pose); previous = pose; }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [audio, playing]);

  const pose = playing ? framePose : editing && resting ? 'smile' : mouthPoseAt(animation.mouthCues, time);
  return <Mouth pose={pose} playful={idle} trackEyes className="animated-mouth" />;
}
