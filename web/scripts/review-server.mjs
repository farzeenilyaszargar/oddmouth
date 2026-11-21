// Serve the ignored review files over loopback. Files never enter the static export.
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline } from 'node:stream/promises';

const runtime = fileURLToPath(new URL('../node_modules/onnxruntime-web/dist/', import.meta.url));
const root = fileURLToPath(new URL('../../outputs/training-review/', import.meta.url));

createServer(async (req, res) => {
  const path = req.url?.split('?')[0] ?? '';
  const runtimeAsset = /^\/runtime\/(ort-wasm-simd-threaded\.(?:mjs|wasm))$/.exec(path);
  const reviewAsset = /^\/(?:index\.json|[a-zA-Z0-9_-]+\/(?:[1-3]-(?:reference|output)\.wav|model\/(?:model\.json|(?:text|flow|vocoder)\.onnx)))$/.test(path);
  if (!['GET', 'HEAD'].includes(req.method) || (!runtimeAsset && !reviewAsset)) {
    res.writeHead(404).end();
    return;
  }
  const file = runtimeAsset ? join(runtime, runtimeAsset[1]) : join(root, path);
  let size;
  try { ({ size } = await stat(file)); } catch { res.writeHead(404).end(); return; }
  const types = { wav: 'audio/wav', json: 'application/json', wasm: 'application/wasm', mjs: 'text/javascript' };
  const extension = path.split('.').pop();
  const headers = {
    'Content-Type': types[extension] ?? 'application/octet-stream',
    'Cache-Control': extension === 'json' ? 'no-store' : 'private, max-age=86400',
    'Accept-Ranges': 'bytes',
  };
  let start = 0;
  let end = size - 1;
  if (req.headers.range) {
    const match = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range);
    if (match) {
      start = Number(match[1]);
      if (match[2]) end = Math.min(end, Number(match[2]));
    }
    if (!match || start > end) {
      res.writeHead(416, { 'Content-Range': `bytes */${size}` }).end();
      return;
    }
    headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
  }
  headers['Content-Length'] = end - start + 1;
  res.writeHead(req.headers.range ? 206 : 200, headers);
  if (req.method === 'HEAD') { res.end(); return; }
  await pipeline(createReadStream(file, { start, end }), res).catch(() => res.destroy());
}).listen(3001, '127.0.0.1', () => console.log('Training review files listening on loopback port 3001'));
