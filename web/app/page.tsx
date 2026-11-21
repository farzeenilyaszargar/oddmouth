'use client';

import { useRef, useState } from 'react';

const SAMPLE = 'Some words are better out loud. Give your ideas a voice with Oddmouth.';
const bars = Array.from({ length: 72 }, (_, i) => 14 + Math.abs(Math.sin(i * 1.8) * Math.cos(i * .47)) * 31);
const clock = (seconds: number) => `0:${Math.floor(seconds).toString().padStart(2, '0')}`;

function Soundmark({ small = false }: { small?: boolean }) {
  return <span className={small ? 'soundmark small' : 'soundmark'} aria-hidden="true"><i /><i /><i /><i /></span>;
}

export default function Home() {
  const audio = useRef<HTMLAudioElement>(null);
  const [text, setText] = useState(SAMPLE);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(5);
  const [error, setError] = useState('');
  const edited = text !== SAMPLE;

  async function playPause() {
    const player = audio.current;
    if (!player) return;
    if (!player.paused) { player.pause(); return; }
    if (player.ended) player.currentTime = 0;
    try { await player.play(); setError(''); }
    catch { setError('Couldn’t play the sample. Try downloading it instead.'); }
  }

  function reset() {
    setText(SAMPLE);
    audio.current?.pause();
    if (audio.current) audio.current.currentTime = 0;
    setTime(0);
    setError('');
  }

  return (
    <div className="site">
      <header className="header">
        <a className="brand" href="/" aria-label="Oddmouth home"><Soundmark />oddmouth<span className="brand-period">.</span></a>
        <span className="header-note">A voice for everyone.</span>
      </header>

      <main>
        <div className="intro">
          <span className="eyebrow">TEXT TO SPEECH, OPEN TO EVERYONE</span>
          <h1>Small model.<br /><em>Big mouth.</em></h1>
          <p>Turn a little text into something worth hearing.<br className="desktop-break" /> Free to use. Easy to love.</p>
        </div>

        <section className="studio" aria-label="Text to speech demo">
          <div className="editor">
            <div className="editor-top"><label htmlFor="words">Your words</label><span className="demo-label">Web demo</span></div>
            <textarea id="words" value={text} maxLength={1000} onChange={event => setText(event.target.value)} placeholder="Something on your mind? Put it into words." spellCheck={false} />
            <div className="editor-bottom"><span>{text.length.toLocaleString()} / 1,000</span><button className="text-button" onClick={reset}>Reset sample</button></div>
          </div>

          <div className="audio-section">
            <div className="audio-heading"><span><Soundmark small /> A little preview</span><span>5 sec · WAV</span></div>
            <div className="player">
              <button className="play" onClick={playPause} aria-label={playing ? 'Pause demo' : 'Play demo'}>
                {playing ? <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg> : <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5a1 1 0 0 1 1.5-.87l10 6.5a1 1 0 0 1 0 1.74l-10 6.5A1 1 0 0 1 8 18.5z" /></svg>}
              </button>
              <div className="timeline">
                <div className="waveform" aria-hidden="true">{bars.map((height, i) => <span key={i} style={{ height: `${height}px`, background: i / bars.length < time / duration ? '#695180' : undefined }} />)}</div>
                <input type="range" min="0" max={duration} step="0.01" value={time} aria-label="Seek demo audio" aria-valuetext={`${clock(time)} of ${clock(duration)}`} onChange={event => { const value = Number(event.target.value); if (audio.current) audio.current.currentTime = value; setTime(value); }} />
              </div>
              <span className="time">{clock(time)} <span>/ {clock(duration)}</span></span>
              <a className="download" href="/audio/oddmouth-demo.wav" download="oddmouth-demo.wav" aria-label="Download five-second demo WAV"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 16v4h14v-4" /></svg><span>Download</span></a>
            </div>
            <audio ref={audio} src="/audio/oddmouth-demo.wav" preload="metadata" onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} onTimeUpdate={event => setTime(event.currentTarget.currentTime)} onLoadedMetadata={event => { if (Number.isFinite(event.currentTarget.duration)) setDuration(event.currentTarget.duration); }} onError={() => setError('The sample couldn’t load. Please refresh and try again.')} />
          </div>
        </section>
        <p className="demo-note" role="status">{error || (edited ? 'Custom voice generation is coming soon. You can listen to the sample below.' : 'A pre-recorded sample for now. The Oddmouth voice is on its way.')}</p>
        <div className="promise"><span>No sign-up.</span><span>No paywall.</span><span>Just a voice.</span></div>
      </main>

      <footer><span>A little odd. A lot to say.</span><a href="https://github.com/farzeenilyaszargar/oddmouth" target="_blank" rel="noreferrer">Follow the build <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.86c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.03A9.58 9.58 0 0 1 12 6.83c.85 0 1.71.11 2.51.34 1.91-1.3 2.75-1.03 2.75-1.03.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2z" /></svg></a></footer>
    </div>
  );
}
