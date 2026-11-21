'use client';

import { useEffect, useState } from 'react';

type Review = { id: string; step: number; vocoderStep: number };
type Model = { acousticStep: number; vocoderStep: number };

export default function VoicePreview() {
  const [runs, setRuns] = useState<(Review & Model)[]>([]);
  const [selected, setSelected] = useState('');
  const [text, setText] = useState('Hey everyone, welcome back.');
  const [status, setStatus] = useState('Looking for saved voice checkpoints…');
  const [pending, setPending] = useState(false);
  const [output, setOutput] = useState('');

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch('/training-files/index.json', { signal: controller.signal, cache: 'no-store' });
        if (!response.ok) throw new Error('Preview unavailable');
        const rows: Review[] = await response.json();
        const available = await Promise.all(rows.map(async row => {
          const model = await fetch(`/training-files/${row.id}/model/model.json`, { signal: controller.signal });
          return model.ok ? { ...row, ...await model.json() as Model } : null;
        }));
        const ready = available.filter(row => row !== null);
        setRuns(ready);
        setStatus(ready.length ? '' : 'No voice checkpoints are ready to preview.');
      } catch {
        if (!controller.signal.aborted) setStatus('The local preview is unavailable. Check the local review server and refresh.');
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  useEffect(() => () => {
    if (output) URL.revokeObjectURL(output);
  }, [output]);

  const run = runs.find(row => row.id === selected) ?? runs[0];

  async function generate() {
    if (!run || pending || !text.trim()) return;
    setPending(true);
    setOutput('');
    setStatus('Loading voice checkpoint…');
    try {
      const { synthesize } = await import('./synthesize');
      const audio = await synthesize(run.id, text, () => setStatus('Generating audio…'));
      setOutput(URL.createObjectURL(audio));
      setStatus('Audio ready.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Couldn’t generate audio.');
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="site">
      <header className="header"><a className="brand" href="/">oddmouth</a><a className="nav-link" href="/">Back to editor</a></header>
      <main><div className="workspace training-review">
        <div className="intro"><h1>Test the voice</h1></div>
        {process.env.NODE_ENV !== 'development' ? <p>Voice checkpoints are available on the local development site.</p> :
          <>
            {run && <>
              <label htmlFor="training-run">Checkpoint</label>
              <select id="training-run" value={run.id} disabled={pending} onChange={event => {
                setSelected(event.target.value);
                setOutput('');
                setStatus('');
              }}>
                {runs.map(row => <option value={row.id} key={row.id}>
                  Acoustic {row.acousticStep.toLocaleString()} · Vocoder {row.vocoderStep.toLocaleString()}
                </option>)}
              </select>
              <p>Try the same short sentence on different checkpoints to hear how the voice changes.</p>
              <section className="studio" aria-label="Voice checkpoint preview">
                <form className="editor" onSubmit={event => { event.preventDefault(); void generate(); }}>
                  <div className="editor-top"><label htmlFor="preview-text">Your text</label></div>
                  <textarea id="preview-text" value={text} maxLength={160} disabled={pending}
                    onChange={event => setText(event.target.value)} />
                  <div className="editor-bottom"><span>{text.length} / 160</span>
                    <button className="generate-button" disabled={pending || !text.trim()}>
                      {pending ? 'Working…' : 'Generate'}
                    </button>
                  </div>
                </form>
                {output && <div className="player">
                  <audio src={output} controls aria-label="Generated voice" />
                  <a className="download" href={output} download="oddmouth-preview.wav">Download</a>
                </div>}
              </section>
            </>}
            <p role="status">{status}</p>
          </>}
      </div></main>
    </div>
  );
}
