export type AudioSettings = {
  effect: 'natural' | 'radio' | 'telephone';
  speed: number;
  volume: number;
  tone: number;
  background: 'none' | 'rain' | 'vinyl';
  noise: number;
};
export const DEFAULT_AUDIO: AudioSettings = { effect: 'natural', speed: 1, volume: 1, tone: 20000, background: 'none', noise: .12 };
export const originalAudio = (s: AudioSettings) => s.effect === 'natural' && s.speed === 1 && s.volume === 1 && s.tone === 20000 && s.background === 'none';
export const outputFrames = (length: number, speed: number) => Math.max(1, Math.ceil(length / speed));

type Samples = Pick<AudioBuffer, 'length' | 'numberOfChannels' | 'sampleRate' | 'getChannelData'>;
export function wavBytes(audio: Samples): ArrayBuffer {
  const channels = audio.numberOfChannels;
  const output = new ArrayBuffer(44 + audio.length * channels * 2);
  const view = new DataView(output);
  const word = (offset: number, text: string) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  word(0, 'RIFF'); view.setUint32(4, output.byteLength - 8, true); word(8, 'WAVE'); word(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, channels, true);
  view.setUint32(24, audio.sampleRate, true); view.setUint32(28, audio.sampleRate * channels * 2, true);
  view.setUint16(32, channels * 2, true); view.setUint16(34, 16, true); word(36, 'data');
  view.setUint32(40, output.byteLength - 44, true);
  const samples = Array.from({ length: channels }, (_, channel) => audio.getChannelData(channel));
  let offset = 44;
  for (let frame = 0; frame < audio.length; frame++) for (const channel of samples) {
    const value = Math.max(-1, Math.min(1, channel[frame]));
    view.setInt16(offset, Math.round(value * (value < 0 ? 32768 : 32767)), true); offset += 2;
  }
  return output;
}

export async function renderAudio(input: AudioBuffer, settings: AudioSettings): Promise<ArrayBuffer> {
  const ctx = new OfflineAudioContext(input.numberOfChannels, outputFrames(input.length, settings.speed), input.sampleRate);
  const source = ctx.createBufferSource(); source.buffer = input; source.playbackRate.value = settings.speed;
  const master = ctx.createGain(); master.gain.value = settings.volume; master.connect(ctx.destination);
  let voice: AudioNode = source;
  if (settings.effect !== 'natural') {
    const high = ctx.createBiquadFilter(); high.type = 'highpass'; high.frequency.value = settings.effect === 'radio' ? 350 : 600;
    const low = ctx.createBiquadFilter(); low.type = 'lowpass'; low.frequency.value = settings.effect === 'radio' ? 3400 : 2400;
    high.Q.value = low.Q.value = .7; voice.connect(high); high.connect(low); voice = low;
  }
  const tone = ctx.createBiquadFilter(); tone.type = 'lowpass'; tone.frequency.value = Math.min(settings.tone, input.sampleRate / 2 - 1); tone.Q.value = .7;
  voice.connect(tone); tone.connect(master);
  if (settings.background !== 'none' && settings.noise > 0) {
    const noise = ctx.createBuffer(1, ctx.length, ctx.sampleRate);
    const samples = noise.getChannelData(0);
    let seed = 937; let brown = 0;
    const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
    for (let i = 0; i < samples.length; i++) {
      const white = random() * 2 - 1;
      brown = (brown + .035 * white) / 1.035;
      samples[i] = settings.background === 'rain' ? brown * 3 + white * .15 : white * .12 + (random() > .998 ? white * .8 : 0);
    }
    const background = ctx.createBufferSource(); background.buffer = noise;
    const gain = ctx.createGain(); gain.gain.setValueAtTime(0, 0); gain.gain.linearRampToValueAtTime(settings.noise, .02);
    gain.gain.setValueAtTime(settings.noise, Math.max(.02, noise.duration - .03)); gain.gain.linearRampToValueAtTime(0, noise.duration);
    background.connect(gain); gain.connect(master); background.start();
  }
  source.start();
  return wavBytes(await ctx.startRendering());
}
