import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const binary = process.argv[2] || 'rhubarb';
const audio = join(root, 'public/audio/oddmouth-demo.wav');
const transcript = join(root, 'demo/transcript.txt');
const temporary = mkdtempSync(join(tmpdir(), 'oddmouth-cues-'));
try {
  const output = join(temporary, 'cues.json');
  const version = execFileSync(binary, ['--version'], { encoding: 'utf8' }).trim();
  execFileSync(binary, ['-f', 'json', '-r', 'pocketSphinx', '--extendedShapes', 'GHX', '-d', transcript, '-o', output, audio], { stdio: 'inherit' });
  const raw = JSON.parse(readFileSync(output, 'utf8'));
  const result = {
    generator: version,
    source: 'https://github.com/DanielSWolf/rhubarb-lip-sync',
    audio: '/audio/oddmouth-demo.wav',
    audioSha256: createHash('sha256').update(readFileSync(audio)).digest('hex'),
    transcript: readFileSync(transcript, 'utf8').trim(),
    duration: raw.metadata.duration,
    mouthCues: raw.mouthCues,
  };
  writeFileSync(join(root, 'demo/lip-sync.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(`Generated ${result.mouthCues.length} audio-aligned mouth cues.`);
} finally {
  rmSync(temporary, { recursive: true, force: true });
}
