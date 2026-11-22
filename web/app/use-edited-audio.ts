'use client';
import { useEffect, useRef, useState, type RefObject } from 'react';
import { originalAudio, renderAudio, type AudioSettings } from './lib/audio-effects';

/**
 * Apply the More-panel effects to `source` (the bundled sample or generated speech).
 * The caller owns `source`; this hook only revokes the edited URLs it creates.
 */
export function useEditedAudio(audio: RefObject<HTMLAudioElement | null>, source: string, settings: AudioSettings, onError: (message: string) => void) {
  const [output, setOutput] = useState({ url: source, speed: 1 });
  const [processing, setProcessing] = useState(false);
  const decoded = useRef<{ source: string; buffer: Promise<AudioBuffer> } | null>(null);
  const appliedSpeed = useRef(1);
  const pending = useRef<{ time: number; resume: boolean } | null>(null);
  const appliedSource = useRef(source);
  useEffect(() => {
    let cancelled = false;
    setProcessing(true);
    const timer = setTimeout(async () => {
      try {
        let url = source;
        if (!originalAudio(settings)) {
          if (decoded.current?.source !== source) {
            decoded.current = {
              source,
              buffer: (async () => {
                const response = await fetch(source);
                if (!response.ok) throw new Error('Audio download failed');
                return new OfflineAudioContext(1, 1, 22050).decodeAudioData(await response.arrayBuffer());
              })(),
            };
          }
          const bytes = await renderAudio(await decoded.current.buffer, settings);
          if (cancelled) return;
          url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
        }
        if (cancelled) return;
        const player = audio.current;
        if (url === source && player?.getAttribute('src') === source) { setProcessing(false); onError(''); return; }
        // New speech plays from the start; a settings change keeps the listening position.
        pending.current = appliedSource.current === source
          ? { time: (player?.currentTime ?? 0) * appliedSpeed.current / settings.speed, resume: Boolean(player && !player.paused && !player.ended) }
          : { time: 0, resume: true };
        appliedSource.current = source;
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
  }, [audio, source, settings, onError]);

  useEffect(() => () => {
    if (output.url !== source && output.url.startsWith('blob:')) URL.revokeObjectURL(output.url);
  }, [output.url, source]);

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
