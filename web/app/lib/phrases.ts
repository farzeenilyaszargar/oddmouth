/**
 * Split text into short phrases. The model learned from clips of about 8 words
 * (90% under 15), so long sentences are broken at punctuation, then by length.
 */
export function phrases(text: string, maxWords = 14) {
  const result: { text: string; pause: number }[] = [];
  for (const sentence of text.replace(/\s+/g, ' ').trim().split(/(?<=[.!?…])\s+/)) {
    const parts = sentence.split(/(?<=[,;:—])\s+/);
    let current: string[] = [];
    const flush = (pause: number) => {
      if (current.length) result.push({ text: current.join(' '), pause });
      current = [];
    };
    for (const part of parts) {
      const words = part.split(' ').filter(Boolean);
      if (current.length && current.length + words.length > maxWords) flush(0.15);
      for (const word of words) {
        if (current.length >= maxWords) flush(0.15);
        current.push(word);
      }
    }
    flush(0.3);
  }
  return result.filter(part => /[\p{L}\p{N}]/u.test(part.text));
}
