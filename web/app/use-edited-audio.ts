'use client';
import { useEffect, useRef, useState, type RefObject } from 'react';
import { originalAudio, renderAudio, type AudioSettings } from './lib/audio-effects';

const SAMPLE_URL = '/audio/oddmouth-demo.wav';
export function useEditedAudio(audio: RefObject<HTMLAudioElement | null>, settings: AudioSettings, onError: (message: string) => void) {
  const [output, setOutput] = useState({ url: SAMPLE_URL, speed: 1 });
  const [processing, setProcessing] = useState(false);
  const decoded = useRef<Promise<AudioBuffer> | null>(null);
  const appliedSpeed = useRef(1);
  const pending = useRef<{ time: number; resume: boolean } | null>(null);
  useEffect(() => {
    let cancelled = false;
    setProcessing(true);
    const timer = setTimeout(async () => {
      try {
        let url = SAMPLE_URL;
        if (!originalAudio(settings)) {
          decoded.current ??= (async () => {
            const response = await fetch(SAMPLE_URL);
            if (!response.ok) throw new Error('Audio download failed');
            return new OfflineAudioContext(1, 1, 22050).decodeAudioData(await response.arrayBuffer());
          })();
          const bytes = await renderAudio(await decoded.current, settings);
          if (cancelled) return;
          url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
        }
        if (cancelled) return;
        const player = audio.current;
        if (url === SAMPLE_URL && player?.getAttribute('src') === SAMPLE_URL) { setProcessing(false); onError(''); return; }
        pending.current = { time: (player?.currentTime ?? 0) * appliedSpeed.current / settings.speed, resume: Boolean(player && !player.paused && !player.ended) };
        // Pause before replacing the source so playback never uses stale effects.
        player?.pause();
        appliedSpeed.current = settings.speed;
        setOutput({ url, speed: settings.speed });
        onError('');
      } catch {
        decoded.current = null;
        if (!cancelled) onError('Could not apply the audio settings. Please try again.');
      } finally { if (!cancelled) setProcessing(false); }
    }, 180);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [audio, settings, onError]);

  useEffect(() => () => { if (output.url.startsWith('blob:')) URL.revokeObjectURL(output.url); }, [output.url]);

  const loaded = async (player: HTMLAudioElement) => {
    const position = pending.current; pending.current = null;
    if (!position) return;
    player.currentTime = Math.min(position.time, player.duration);
    if (position.resume && !player.ended) {
      try { await player.play(); } catch { onError('Audio is ready. Press play to listen.'); }
    }
  };
  return { ...output, processing, loaded };
}
