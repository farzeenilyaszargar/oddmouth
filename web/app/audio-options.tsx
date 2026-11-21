'use client';
import type { AudioSettings } from './lib/audio-effects';

type Props = { settings: AudioSettings; onChange: (settings: AudioSettings) => void };
export default function AudioOptions({ settings, onChange }: Props) {
  const update = <K extends keyof AudioSettings>(key: K, value: AudioSettings[K]) => onChange({ ...settings, [key]: value });
  return <section id="audio-options" className="audio-options" aria-label="Audio settings">
    <fieldset className="voice-effects"><legend>Voice effect</legend><div>{(['natural', 'radio', 'telephone'] as const).map(effect => <label key={effect}><input type="radio" name="voice-effect" value={effect} checked={settings.effect === effect} onChange={() => update('effect', effect)} /><span>{effect === 'natural' ? 'Natural' : effect === 'radio' ? 'Radio' : 'Telephone'}</span></label>)}</div></fieldset>
    <div className="options-grid">
      <label>Speed <output>{settings.speed.toFixed(2)}×</output><input aria-label="Speed" type="range" min="0.75" max="1.5" step="0.05" value={settings.speed} onChange={event => update('speed', Number(event.target.value))} /></label>
      <label>Volume <output>{Math.round(settings.volume * 100)}%</output><input aria-label="Volume" type="range" min="0" max="1" step="0.05" value={settings.volume} onChange={event => update('volume', Number(event.target.value))} /></label>
      <label>Low-pass filter <output>{settings.tone === 20000 ? 'Off' : `${(settings.tone / 1000).toFixed(1)} kHz`}</output><input aria-label="Low-pass filter" type="range" min="1000" max="20000" step="500" value={settings.tone} onChange={event => update('tone', Number(event.target.value))} /></label>
      <label>Background<select value={settings.background} onChange={event => update('background', event.target.value as AudioSettings['background'])}><option value="none">None</option><option value="rain">Rain texture</option><option value="vinyl">Vinyl noise</option></select></label>
      {settings.background !== 'none' && <label>Background level <output>{Math.round(settings.noise * 100)}%</output><input aria-label="Background level" type="range" min="0" max="0.4" step="0.01" value={settings.noise} onChange={event => update('noise', Number(event.target.value))} /></label>}
    </div>
    <p>Changes apply to playback and download. Speed also changes pitch.</p>
  </section>;
}
