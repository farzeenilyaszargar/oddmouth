"""Export a checkpoint pair for the loopback-only browser training review."""
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
import onnxruntime as ort
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oddmouth.audio import MELS, SR
from oddmouth.model import AcousticModel, Vocoder
from oddmouth.text import INDEX, BLANK, UNK, VOCAB_SIZE
from oddmouth.throttle import limit_threads
from scripts.speak import load


class ExportAttention(nn.Module):
    """Express self-attention directly so sequence length stays dynamic in ONNX."""
    def __init__(self, attention):
        super().__init__()
        self.attention = attention
        self.heads = attention.num_heads
        self.width = attention.embed_dim // self.heads

    def forward(self, query, key, value, key_padding_mask, need_weights=False):
        batch, length, _ = query.shape
        q, k, v = F.linear(query, self.attention.in_proj_weight,
                           self.attention.in_proj_bias).chunk(3, dim=-1)
        q, k, v = (part.reshape(batch, length, self.heads, self.width).transpose(1, 2)
                   for part in (q, k, v))
        scores = (q @ k.transpose(-1, -2)) * self.width ** -.5
        scores = scores.masked_fill(key_padding_mask[:, None, None, :], float('-inf'))
        value = (scores.softmax(dim=-1) @ v).transpose(1, 2).reshape(batch, length, -1)
        return self.attention.out_proj(value), None


class TextEncoder(nn.Module):
    def __init__(self, acoustic):
        super().__init__()
        self.acoustic = acoustic

    def forward(self, tokens):
        lengths = torch.ones_like(tokens).sum(1)
        features, mask = self.acoustic.encode(tokens, lengths)
        return (self.acoustic.duration(features, mask), self.acoustic.to_mu(features),
                self.acoustic.to_cond(features))


class FlowStep(nn.Module):
    def __init__(self, acoustic):
        super().__init__()
        self.acoustic = acoustic

    def forward(self, noise, prior, condition, time):
        mask = torch.ones_like(prior[:, :, 0], dtype=torch.bool)
        return self.acoustic.velocity(noise, prior, condition, time, mask)


def export(module, args, check_args, out, inputs, outputs, axes):
    torch.onnx.export(module.eval(), args, out, input_names=inputs, output_names=outputs,
                      dynamic_axes=axes, opset_version=18, dynamo=False)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    session = ort.InferenceSession(str(out), sess_options=options, providers=['CPUExecutionProvider'])
    expected = module(*check_args)
    if not isinstance(expected, tuple):
        expected = (expected,)
    values = dict(zip(inputs, (tensor.numpy() for tensor in check_args)))
    for actual, target in zip(session.run(None, values), expected):
        np.testing.assert_allclose(actual, target.numpy(), atol=2e-4, rtol=1e-3)


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acoustic', type=Path, default=ROOT / 'runs/acoustic/last.pt')
    parser.add_argument('--vocoder', type=Path, default=ROOT / 'runs/vocoder/last.pt')
    parser.add_argument('--review-id', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.review_id):
        parser.error('Review ID must use letters, digits, dashes or underscores')
    config = json.loads((ROOT / 'configs/oddmouth.json').read_text())
    limit_threads(config['cpu_share'])
    # Use decomposed attention operators instead of PyTorch's inference-only fused path.
    torch.backends.mha.set_fastpath_enabled(False)
    torch.manual_seed(2026)
    acoustic, acoustic_step = load(args.acoustic, lambda arch: AcousticModel(arch, VOCAB_SIZE))
    vocoder, vocoder_step = load(args.vocoder, Vocoder)
    review_dir = ROOT / 'outputs/training-review' / args.review_id
    if not review_dir.is_dir():
        raise ValueError('Export the listening review first')
    manifest = json.loads((review_dir.parent / 'index.json').read_text())
    review = next(row for row in manifest if row['id'] == args.review_id)
    if review['stage'] == 'acoustic' and review['step'] != acoustic_step:
        raise ValueError('Acoustic checkpoint step differs from the listening review')
    if review['vocoderStep'] != vocoder_step:
        raise ValueError('Vocoder checkpoint step differs from the listening review')

    frame_axis = {1: 'frames'}
    tokens_axis = {1: 'tokens'}
    frames = torch.randn(1, 27, MELS)
    check_frames = torch.randn(1, 49, MELS)
    width = acoustic.decoder_width
    tokens = torch.randint(3, VOCAB_SIZE, (1, 41))
    encoder = TextEncoder(acoustic)
    flow = FlowStep(acoustic)
    check_flow = (check_frames, check_frames, torch.randn(1, 49, width), torch.tensor([.5]))
    expected = (*encoder(tokens), flow(*check_flow))
    for block in (*acoustic.encoder, *acoustic.decoder):
        block.attn = ExportAttention(block.attn)
    for result, reference in zip((*encoder(tokens), flow(*check_flow)), expected):
        torch.testing.assert_close(result, reference, atol=2e-5, rtol=1e-4)
    target = review_dir / 'model'
    if target.exists():
        raise ValueError(f'Browser export already exists at {target}')
    with tempfile.TemporaryDirectory(dir=review_dir) as tmp:
        folder = Path(tmp) / 'model'
        folder.mkdir()
        export(encoder, (torch.randint(3, VOCAB_SIZE, (1, 17)),), (tokens,),
               folder / 'text.onnx', ['tokens'], ['duration', 'prior', 'condition'],
               {name: tokens_axis for name in ('tokens', 'duration', 'prior', 'condition')})
        export(flow, (frames, frames, torch.randn(1, 27, width), torch.zeros(1)), check_flow,
               folder / 'flow.onnx', ['noise', 'prior', 'condition', 'time'], ['velocity'],
               {name: frame_axis for name in ('noise', 'prior', 'condition', 'velocity')})
        export(vocoder, (frames.transpose(1, 2).contiguous(),),
               (check_frames.transpose(1, 2).contiguous(),), folder / 'vocoder.onnx',
               ['mel'], ['wave'], {'mel': {2: 'frames'}, 'wave': {2: 'samples'}})
        (folder / 'model.json').write_text(json.dumps({
            'acousticStep': acoustic_step, 'vocoderStep': vocoder_step,
            'sampleRate': SR, 'melMean': acoustic.mel_mean.tolist(), 'melStd': acoustic.mel_std.tolist(),
            'symbols': INDEX, 'blank': BLANK, 'unknown': UNK,
            'steps': config['training']['synthesis_flow_steps'],
        }))
        folder.rename(target)
    print(f'Exported and checked ONNX graphs at {target}')


if __name__ == '__main__':
    main()
