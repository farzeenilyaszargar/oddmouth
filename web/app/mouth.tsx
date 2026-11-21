'use client';

import { useEffect, useRef } from 'react';
import type { MouthPose } from './lib/lip-sync';

type MouthProps = { pose?: MouthPose; className?: string; trackEyes?: boolean; playful?: boolean };

// Original vector artwork based on the supplied three-tooth face. The sound
// groups follow Rhubarb's A-H/X convention; recognition remains approximate.
export default function Mouth({ pose = 'smile', className = '', trackEyes = false, playful = false }: MouthProps) {
  const face = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (!trackEyes) return;
    let frame = 0;
    let pointer = { x: 0, y: 0 };
    const follow = () => {
      frame = 0;
      const element = face.current;
      if (!element) return;
      const bounds = element.getBoundingClientRect();
      const dx = pointer.x - (bounds.left + bounds.width / 2);
      const dy = pointer.y - (bounds.top + bounds.height * .175);
      const distance = Math.hypot(dx, dy);
      const strength = Math.min(distance / 160, 1);
      element.style.setProperty('--gaze-x', `${distance ? dx / distance * strength * 13 : 0}px`);
      element.style.setProperty('--gaze-y', `${distance ? dy / distance * strength * 9 : 0}px`);
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType === 'touch') return;
      pointer = { x: event.clientX, y: event.clientY };
      if (!frame) frame = requestAnimationFrame(follow);
    };
    const reset = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      face.current?.style.setProperty('--gaze-x', '0px');
      face.current?.style.setProperty('--gaze-y', '0px');
    };
    const leave = (event: PointerEvent) => { if (!event.relatedTarget) reset(); };
    window.addEventListener('pointermove', move, { passive: true });
    window.addEventListener('pointerout', leave);
    window.addEventListener('blur', reset);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerout', leave);
      window.removeEventListener('blur', reset);
    };
  }, [trackEyes]);
  const teeth = <path d="M60 82L120 92C119 130 59 134 60 82ZM130 94Q160 100 190 94C194 140 126 140 130 94ZM200 92L260 82C261 134 201 130 200 92Z" fill="white" />;
  const expressions = {
    smile: <g><path d="M20 93C12 51 76 77 128 84Q160 91 192 84C244 77 308 51 300 93C312 150 225 190 160 190C95 190 8 150 20 93Z" fill="currentColor" />{teeth}</g>,
    closed: <g><path d="M35 111Q160 142 285 111" stroke="currentColor" strokeWidth="12" strokeLinecap="round" /><path d="M130 142Q160 149 190 142" stroke="currentColor" strokeWidth="4" strokeLinecap="round" /></g>,
    teeth: <g><path d="M21 92Q28 61 100 80Q160 99 220 80Q292 61 299 92Q312 157 160 176Q8 157 21 92Z" fill="currentColor" /><path d="M51 89Q160 125 269 89L260 127Q160 164 60 127Z" fill="white" /><path d="M104 103L103 143M158 110V150M215 103L216 143M56 113Q160 145 264 113" stroke="currentColor" strokeWidth="5" /></g>,
    open: <g><path d="M48 101C38 73 85 78 128 86Q160 93 192 86C235 78 282 73 272 101C272 151 221 171 160 171C99 171 48 151 48 101Z" fill="currentColor" /><path d="M79 91L125 99Q122 124 101 121Q80 119 79 91ZM136 101Q160 105 184 101Q185 132 160 132Q135 132 136 101ZM195 99L241 91Q240 119 219 121Q198 124 195 99Z" fill="white" /></g>,
    wide: <g><path d="M20 91C16 54 83 76 160 85C237 76 304 54 300 91C314 161 225 196 160 194C95 196 6 161 20 91Z" fill="currentColor" />{teeth}</g>,
    round: <g><path d="M110 86C110 60 210 60 210 86C236 130 204 188 160 188C116 188 84 130 110 86Z" fill="currentColor" /><path d="M127 80Q160 70 193 80L188 100Q160 109 132 100Z" fill="white" /></g>,
    pucker: <g><path d="M133 91Q160 77 187 91C215 118 200 169 160 174C120 169 105 118 133 91Z" fill="currentColor" /><ellipse cx="160" cy="128" rx="15" ry="27" fill="white" /><path d="M116 107L101 101M204 107L219 101" stroke="currentColor" strokeWidth="4" strokeLinecap="round" /></g>,
    bite: <g><path d="M38 100Q160 72 282 100Q280 155 160 163Q40 155 38 100Z" fill="currentColor" /><path d="M65 99Q160 84 255 99L243 129Q160 147 77 129Z" fill="white" /><path d="M125 94V133M192 94V133M59 129Q160 156 261 129" stroke="currentColor" strokeWidth="5" strokeLinecap="round" /></g>,
  };
  return <svg ref={face} className={`mouth ${trackEyes ? 'living-mouth' : ''} ${playful ? 'idle-mode' : ''} ${className}`} data-pose={pose} data-mode={playful ? 'idle' : 'speech'} viewBox="0 0 320 200" fill="none" aria-hidden="true">
    <g className="eyes"><g className="eye-blink"><g className="eye-left"><circle cx="76" cy="35" r="16" fill="currentColor" /></g><g className="eye-right"><circle cx="244" cy="35" r="16" fill="currentColor" /></g></g></g>
    {playful ? <g className="idle-performance">{expressions.smile}</g> : expressions[pose]}
  </svg>;
}
