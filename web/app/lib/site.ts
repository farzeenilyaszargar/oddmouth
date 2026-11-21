const configuredUrl = process.env.SITE_URL;
export const siteUrl = configuredUrl ? new URL(configuredUrl) : undefined;
if (siteUrl && !['http:', 'https:'].includes(siteUrl.protocol)) {
  throw new Error('SITE_URL must use http or https.');
}
const localHost = siteUrl && /^(localhost|127\..*|\[::1\])$/.test(siteUrl.hostname);
export const indexable = Boolean(siteUrl && !localHost && process.env.SITE_INDEXABLE !== 'false');
export const siteTitle = 'Oddmouth | Free Text to Speech';
export const siteDescription = 'Oddmouth is a free text-to-speech project. Listen to a voice sample, download the audio, and try speech-synced mouth animation in the web demo.';
