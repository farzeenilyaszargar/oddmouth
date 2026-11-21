'use client';

import { useRef, useState } from 'react';
import Mouth from './mouth';
import SpeakingMouth from './speaking-mouth';
import animation from '../demo/lip-sync.json';

const SAMPLE = animation.transcript;
const clock = (seconds: number) => `0:${Math.floor(seconds).toString().padStart(2, '0')}`;


export default function Home() {
  const audio = useRef<HTMLAudioElement>(null);
  const about = useRef<HTMLDialogElement>(null);
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
        <a className="brand" href="/" aria-label="Oddmouth home">oddmouth</a>
        <nav className="nav-links" aria-label="Main navigation"><a className="nav-link" href="https://github.com/farzeenilyaszargar/oddmouth" target="_blank" rel="noreferrer">GitHub</a><button className="about-button" onClick={() => about.current?.showModal()}>About</button></nav>
      </header>

      <main>
        <div className="workspace">
          <div className="intro"><h1>Small model. Big mouth.</h1><p>Free text to speech.</p></div>
          <div className={`character ${playing ? 'speaking' : ''}`}>
            <SpeakingMouth audio={audio} playing={playing} time={time} /><Mouth className="still-mouth" />
          </div>

          <section className="studio" aria-label="Text to speech demo">
            <div className="editor">
              <div className="editor-top"><label htmlFor="words">Your words</label><span>Demo</span></div>
              <textarea id="words" value={text} maxLength={1000} onChange={event => setText(event.target.value)} placeholder="Give me something to say." spellCheck={false} />
              <div className="editor-bottom"><span>{text.length.toLocaleString()} / 1,000</span><button className="text-button" onClick={reset}>Reset sample</button></div>
            </div>
            <div className="player">
              <button className="play" onClick={playPause} aria-label={playing ? 'Pause demo' : 'Play demo'}>
                {playing ? <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg> : <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5a1 1 0 0 1 1.5-.87l10 6.5a1 1 0 0 1 0 1.74l-10 6.5A1 1 0 0 1 8 18.5z" /></svg>}
              </button>
              <div className="track"><span className="track-label">{playing ? 'Speaking' : 'Voice preview'}<span className="time">{clock(time)} / {clock(duration)}</span></span><input type="range" min="0" max={duration} step="0.01" value={time} aria-label="Seek demo audio" aria-valuetext={`${clock(time)} of ${clock(duration)}`} style={{ background: `linear-gradient(to right, #111 ${time / duration * 100}%, #e5e5e5 ${time / duration * 100}%)` }} onChange={event => { const value = Number(event.target.value); if (audio.current) audio.current.currentTime = value; setTime(value); }} /></div>
              <a className="download" href="/audio/oddmouth-demo.wav" download="oddmouth-demo.wav" aria-label="Download five-second demo WAV"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 16v4h14v-4" /></svg><span>Download</span></a>
            </div>
            <audio ref={audio} src="/audio/oddmouth-demo.wav" preload="metadata" onPlay={() => setPlaying(true)} onPause={event => { setPlaying(false); setTime(event.currentTarget.currentTime); }} onEnded={event => { setPlaying(false); setTime(event.currentTarget.currentTime); }} onTimeUpdate={event => setTime(event.currentTarget.currentTime)} onLoadedMetadata={event => { if (Number.isFinite(event.currentTarget.duration)) setDuration(event.currentTarget.duration); }} onError={() => setError('The sample couldn’t load. Please refresh and try again.')} />
          </section>
          <p className="demo-note" role="status">{error || (edited ? 'Custom speech generation is not available yet.' : 'Demo recording. 5 seconds.')}</p>
        </div>
      </main>

      <dialog ref={about} className="about-dialog" aria-labelledby="about-title" onClick={event => { if (event.target === about.current) about.current?.close(); }}>
        <div className="dialog-top"><Mouth /><button aria-label="Close about" onClick={() => about.current?.close()}>✕</button></div>
        <h2 id="about-title">About Oddmouth</h2>
        <p>Oddmouth is a free text-to-speech project. This demo plays a prerecorded sample. Custom speech generation is not connected yet.</p>
        <p>The mouth follows sounds detected in the recording. Its timing is approximate.</p>
        <a href="https://github.com/farzeenilyaszargar/oddmouth" target="_blank" rel="noreferrer">Source code on GitHub</a>
      </dialog>
    </div>
  );
}
