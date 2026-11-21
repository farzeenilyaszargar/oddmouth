'use client';

import { useEffect, useState, type RefObject } from 'react';
import Mouth from './mouth';
import { mouthPoseAt, type MouthPose } from './lib/lip-sync';
import animation from '../demo/lip-sync.json';

type Props = { audio: RefObject<HTMLAudioElement | null>; playing: boolean; time: number; duration: number; editing: boolean };

export default function SpeakingMouth({ audio, playing, time, duration, editing }: Props) {
  const [framePose, setFramePose] = useState<MouthPose>('smile');
  const [idlePose, setIdlePose] = useState<MouthPose>('smile');
  const resting = time === 0 || time >= duration;
  const idle = !playing && resting && !editing;

  useEffect(() => {
    if (!idle || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const routine: { pose: MouthPose; hold: number }[] = [
      { pose: 'smile', hold: 2800 },
      { pose: 'tongue', hold: 800 },
      { pose: 'smirk', hold: 1100 },
      { pose: 'smile', hold: 3300 },
      { pose: 'pucker', hold: 650 },
      { pose: 'round', hold: 450 },
      { pose: 'smile', hold: 2700 },
      { pose: 'teeth', hold: 700 },
      { pose: 'smirk', hold: 900 },
    ];
    let step = 0;
    let timer: ReturnType<typeof setTimeout>;
    const next = () => {
      if (!document.hidden) {
        setIdlePose(routine[step].pose);
        timer = setTimeout(next, routine[step].hold);
        step = (step + 1) % routine.length;
      } else timer = setTimeout(next, 1000);
    };
    timer = setTimeout(next, 100);
    return () => clearTimeout(timer);
  }, [idle]);
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

  const pose = playing ? framePose : editing && resting ? 'smile' : idle ? idlePose : mouthPoseAt(animation.mouthCues, time);
  return <Mouth pose={pose} trackEyes className="animated-mouth" />;
}
