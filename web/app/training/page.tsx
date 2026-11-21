'use client';

import { useEffect, useState } from 'react';

type Clip = { text: string; reference: string; output: string };
type Review = { id: string; stage: 'vocoder' | 'acoustic'; step: number; vocoderStep: number; dataset: string; clips: Clip[] };

export default function TrainingReview() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selected, setSelected] = useState('');
  const [status, setStatus] = useState('Loading training runs…');

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch('/training-files/index.json', { signal: controller.signal, cache: 'no-store' });
        if (!response.ok) throw new Error('Review unavailable');
        const rows: Review[] = await response.json();
        setReviews(rows);
        setStatus(rows.length ? '' : 'No runs ready for review yet.');
      } catch {
        if (!controller.signal.aborted) setStatus('No local review is available. Start the review server and refresh.');
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  const review = reviews.find(row => row.id === selected) ?? reviews[0];
  const label = review?.stage === 'vocoder' ? 'Vocoder reconstruction' : 'Text-to-speech output';

  return (
    <div className="site">
      <header className="header"><a className="brand" href="/">oddmouth</a><a className="nav-link" href="/">Back to editor</a></header>
      <main><div className="workspace training-review">
        <div className="intro"><h1>Training review</h1></div>
        {process.env.NODE_ENV !== 'development' ? <p>Listening reviews are available on the local development site.</p> :
          !review ? <p role="status">{status}</p> :
          <>
            <label htmlFor="training-run">Run</label>
            <select id="training-run" value={review.id} onChange={event => setSelected(event.target.value)}>
              {reviews.map(row => <option value={row.id} key={row.id}>
                {row.stage === 'vocoder' ? 'Vocoder' : 'Acoustic'} · Step {row.step.toLocaleString()}
              </option>)}
            </select>
            <p>{review.dataset} · {review.stage === 'vocoder'
              ? 'Compare the same held-out recording with its reconstruction. This run evaluates the audio decoder.'
              : `Generated from held-out text using vocoder step ${review.vocoderStep.toLocaleString()}.`}</p>
            <div key={review.id} className="training-clips">
              {review.clips.map((clip, index) => (
                <article className="studio training-clip" key={clip.reference}>
                  <h2>{clip.text}</h2>
                  <div className="training-audio">
                    <label>Original recording
                      <audio aria-label={`Original recording ${index + 1}`} controls preload="none" src={`/training-files/${review.id}/${clip.reference}`} />
                    </label>
                    <label>{label}
                      <audio aria-label={`${label} ${index + 1}`} controls preload="none" src={`/training-files/${review.id}/${clip.output}`} />
                    </label>
                  </div>
                </article>
              ))}
            </div>
          </>}
      </div></main>
    </div>
  );
}
