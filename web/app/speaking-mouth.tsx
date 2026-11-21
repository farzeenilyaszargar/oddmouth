'use client';

import { useEffect, useState, type RefObject } from 'react';
import Mouth from './mouth';
import { mouthPoseAt, type MouthPose } from './lib/lip-sync';
import animation from '../demo/lip-sync.json';

type Props = { audio: RefObject<HTMLAudioElement | null>; playing: boolean; time: number };

export default function SpeakingMouth({ audio, playing, time }: Props) {
  const [framePose, setFramePose] = useState<MouthPose>('smile');
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

  return <Mouth pose={playing ? framePose : mouthPoseAt(animation.mouthCues, time)} className="animated-mouth" />;
}
