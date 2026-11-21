"""Oddmouth: a ~15M-parameter single-speaker TTS trained from random weights.

Acoustic model (Matcha-TTS-style): transformer text encoder, monotonic
alignment search during training, log-duration predictor, and a
conditional flow-matching mel decoder.

Vocoder (Vocos-style): ConvNeXt blocks over mel frames predict STFT
magnitude and phase; a fixed inverse STFT made of a transposed convolution
turns them into audio. No complex ops, so it runs on MPS and exports to ONNX.

There is no pretrained-weight loading path anywhere in this module.
"""
import math
import time

import torch
from torch import nn
import torch.nn.functional as F

from .audio import FFT, HOP, MELS


def sinusoid(length, width, device, scale=1.0):
    position = torch.arange(length, device=device).float()[:, None] * scale
    freq = torch.exp(torch.arange(0, width, 2, device=device).float() * (-math.log(10000) / width))
    return torch.stack(((position * freq).sin(), (position * freq).cos()), -1).flatten(-2)


def time_embedding(t, width):
    half = width // 2
    freq = torch.exp(torch.arange(half, device=t.device).float() * (-math.log(10000) / half))
    phase = t[:, None] * 1000 * freq[None]
    return torch.cat([phase.sin(), phase.cos()], -1)


def sequence_mask(lengths, maximum=None):
    maximum = int(lengths.max()) if maximum is None else maximum
    return torch.arange(maximum, device=lengths.device)[None] < lengths[:, None]


class Block(nn.Module):
    """Pre-norm self-attention + depthwise conv + MLP, with padding masks."""

    def __init__(self, width, heads, ffn, kernel):
        super().__init__()
        self.norm1, self.norm2, self.norm3 = nn.LayerNorm(width), nn.LayerNorm(width), nn.LayerNorm(width)
        self.attn = nn.MultiheadAttention(width, heads, batch_first=True)
        self.conv = nn.Conv1d(width, width, kernel, padding=kernel // 2, groups=width)
        self.ffn = nn.Sequential(nn.Linear(width, ffn), nn.GELU(), nn.Linear(ffn, width))

    def forward(self, x, mask):
        m = mask[..., None]
        h = self.norm1(x)
        x = x + self.attn(h, h, h, key_padding_mask=~mask, need_weights=False)[0]
        h = self.norm2(x) * m
        x = x + self.conv(h.transpose(1, 2)).transpose(1, 2)
        x = x + self.ffn(self.norm3(x))
        return x * m


class DurationPredictor(nn.Module):
    def __init__(self, width, hidden, kernel=3, dropout=0.1):
        super().__init__()
        self.conv1 = nn.Conv1d(width, hidden, kernel, padding=kernel // 2)
        self.conv2 = nn.Conv1d(hidden, hidden, kernel, padding=kernel // 2)
        self.norm1, self.norm2 = nn.LayerNorm(hidden), nn.LayerNorm(hidden)
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        m = mask[..., None]
        h = x * m
        h = self.drop(self.norm1(F.relu(self.conv1(h.transpose(1, 2)).transpose(1, 2)))) * m
        h = self.drop(self.norm2(F.relu(self.conv2(h.transpose(1, 2)).transpose(1, 2)))) * m
        return self.out(h).squeeze(-1) * mask


@torch.no_grad()
def monotonic_alignment(log_p, token_lengths, frame_lengths):
    """Batched Viterbi monotonic alignment (MAS). log_p [B, N, T] -> path [B, N, T].

    Every token gets at least one frame; frames advance by 0 or 1 token.
    Runs on CPU in a loop over frames, vectorized over batch and tokens.
    """
    device = log_p.device
    log_p = log_p.float().cpu()
    batch, tokens, frames = log_p.shape
    if bool((frame_lengths.cpu() < token_lengths.cpu()).any()):
        raise ValueError('A clip has fewer mel frames than tokens')
    neg = -1e9
    index = torch.arange(tokens)
    log_p = log_p.masked_fill(index[None, :, None] >= token_lengths.cpu()[:, None, None], neg)
    value = torch.full((batch, tokens), neg)
    value[:, 0] = log_p[:, 0, 0]
    advanced = torch.zeros(batch, tokens, frames, dtype=torch.bool)
    for t in range(1, frames):
        previous = F.pad(value[:, :-1], (1, 0), value=neg)
        advanced[:, :, t] = previous > value
        value = torch.maximum(value, previous) + log_p[:, :, t]
        value[:, index > t] = neg
    path = torch.zeros(batch, tokens, frames)
    rows = torch.arange(batch)
    current = token_lengths.cpu().long() - 1
    lengths = frame_lengths.cpu()
    for t in range(frames - 1, -1, -1):
        active = t < lengths
        path[rows[active], current[active], t] = 1
        step = advanced[rows, current, t] & active & (current > 0)
        current = current - step.long()
    return path.to(device)


def path_from_durations(durations, token_mask):
    """Integer durations [B, N] -> hard alignment path [B, N, T] and frame lengths."""
    durations = durations * token_mask
    end = durations.cumsum(1)
    frames = torch.arange(int(end[:, -1].max()), device=durations.device)
    path = (frames[None, None] < end[..., None]) & (frames[None, None] >= (end - durations)[..., None])
    return path.float(), end[:, -1]


class AcousticModel(nn.Module):
    def __init__(self, a, vocab_size):
        super().__init__()
        d, f = a['text_width'], a['decoder_width']
        self.text_width, self.decoder_width, self.time_width = d, f, a['time_width']
        self.embedding = nn.Embedding(vocab_size, d)
        self.encoder = nn.ModuleList([Block(d, a['text_heads'], a['text_ffn'], 5) for _ in range(a['text_layers'])])
        self.encoder_norm = nn.LayerNorm(d)
        self.to_mu = nn.Linear(d, MELS)
        self.to_cond = nn.Linear(d, f)
        self.duration = DurationPredictor(d, a['duration_width'])
        self.decoder_in = nn.Linear(2 * MELS, f)
        self.time = nn.Sequential(nn.Linear(a['time_width'], f), nn.SiLU(), nn.Linear(f, f))
        self.decoder = nn.ModuleList([Block(f, a['decoder_heads'], a['decoder_ffn'], 7)
                                      for _ in range(a['decoder_layers'])])
        self.decoder_norm = nn.LayerNorm(f)
        self.decoder_out = nn.Linear(f, MELS)
        # Training-set mel statistics; set before training, saved in checkpoints.
        self.register_buffer('mel_mean', torch.zeros(MELS))
        self.register_buffer('mel_std', torch.ones(MELS))

    def encode(self, tokens, lengths):
        mask = sequence_mask(lengths, tokens.shape[1])
        x = self.embedding(tokens) + sinusoid(tokens.shape[1], self.text_width, tokens.device)
        for block in self.encoder:
            x = block(x, mask)
        return self.encoder_norm(x) * mask[..., None], mask

    def velocity(self, x_t, mu_y, cond_y, t, frame_mask):
        h = self.decoder_in(torch.cat([x_t, mu_y], -1)) + cond_y
        h = h + self.time(time_embedding(t, self.time_width))[:, None]
        h = h + sinusoid(x_t.shape[1], self.decoder_width, x_t.device)
        for block in self.decoder:
            h = block(h, frame_mask)
        return self.decoder_out(self.decoder_norm(h)) * frame_mask[..., None]

    def normalize(self, mel):  # [B, 80, T] log mel -> [B, T, 80] normalized
        return ((mel - self.mel_mean[:, None]) / self.mel_std[:, None]).transpose(1, 2)

    def losses(self, tokens, token_lengths, mel, frame_lengths, sigma_min=1e-4, *, profile=None):
        x, token_mask = self.encode(tokens, token_lengths)
        y = self.normalize(mel)
        frame_mask = sequence_mask(frame_lengths, y.shape[1])
        mu_x = self.to_mu(x)
        with torch.no_grad():
            # Unit-variance Gaussian log-likelihood of each frame under each token.
            log_p = -0.5 * ((y.square().sum(-1)[:, None, :]) - 2 * mu_x @ y.transpose(1, 2)
                            + mu_x.square().sum(-1)[..., None])
            if profile is not None:
                if log_p.device.type == 'mps':
                    torch.mps.synchronize()
                started = time.monotonic()
            path = monotonic_alignment(log_p, token_lengths, frame_lengths)
            if profile is not None:
                if log_p.device.type == 'mps':
                    torch.mps.synchronize()
                profile['alignment'] = time.monotonic() - started
        durations = path.sum(-1)
        log_w = self.duration(x.detach(), token_mask)
        target_log_w = torch.log(durations + 1e-8) * token_mask
        duration_loss = (log_w - target_log_w).square().sum() / token_lengths.sum()
        align = path.transpose(1, 2)
        mu_y, cond_y = align @ mu_x, align @ self.to_cond(x)
        m = frame_mask[..., None]
        count = frame_mask.sum() * MELS
        prior_loss = (0.5 * ((y - mu_y).square() + math.log(2 * math.pi)) * m).sum() / count
        t = torch.rand(y.shape[0], device=y.device)
        z = torch.randn_like(y)
        x_t = (1 - (1 - sigma_min) * t[:, None, None]) * z + t[:, None, None] * y
        target = y - (1 - sigma_min) * z
        flow_loss = ((self.velocity(x_t, mu_y, cond_y, t, frame_mask) - target).square() * m).sum() / count
        total = flow_loss + prior_loss + duration_loss
        return total, {'flow': flow_loss, 'prior': prior_loss, 'duration': duration_loss}

    @torch.no_grad()
    def synthesize(self, tokens, lengths, steps=8, temperature=0.667, length_scale=1.0, max_frames=4000):
        """Tokens -> log mel [B, 80, T] (denormalized) and frame lengths."""
        x, token_mask = self.encode(tokens, lengths)
        durations = torch.ceil(torch.exp(self.duration(x, token_mask)) * length_scale).clamp_min(1)
        path, frame_lengths = path_from_durations(durations.long() * token_mask, token_mask)
        if int(frame_lengths.max()) > max_frames:
            raise ValueError('Phrase too long; split the text into shorter sentences')
        frame_mask = sequence_mask(frame_lengths, path.shape[-1])
        align = path.transpose(1, 2)
        mu_y, cond_y = align @ self.to_mu(x), align @ self.to_cond(x)
        y = torch.randn_like(mu_y) * temperature
        for i in range(steps):
            t = torch.full((y.shape[0],), i / steps, device=y.device)
            y = y + self.velocity(y, mu_y, cond_y, t, frame_mask) / steps
        mel = y.transpose(1, 2) * self.mel_std[:, None] + self.mel_mean[:, None]
        return mel, frame_lengths


class InverseSTFT(nn.Module):
    """Weighted overlap-add inverse STFT as a fixed transposed convolution.

    Inverts the mel_spectrogram framing: reflect pad (FFT-HOP)/2, hann window,
    center=False. T frames -> T * HOP samples.
    """

    def __init__(self, n_fft=FFT, hop=HOP):
        super().__init__()
        self.n_fft, self.hop = n_fft, hop
        n = torch.arange(n_fft).float()
        k = torch.arange(n_fft // 2 + 1).float()
        angle = 2 * math.pi * k[:, None] * n[None] / n_fft
        scale = torch.full((len(k), 1), 2.0)
        scale[0], scale[-1] = 1.0, 1.0
        window = torch.hann_window(n_fft)
        basis = torch.cat([scale * angle.cos(), -scale * angle.sin()]) / n_fft * window
        self.register_buffer('basis', basis[:, None], persistent=False)
        self.register_buffer('window_sq', window.square()[None, None], persistent=False)

    def forward(self, real, imag):
        frames = real.shape[-1]
        wave = F.conv_transpose1d(torch.cat([real, imag], 1), self.basis, stride=self.hop)
        ones = torch.ones(1, 1, frames, device=real.device, dtype=real.dtype)
        envelope = F.conv_transpose1d(ones, self.window_sq, stride=self.hop)
        start = (self.n_fft - self.hop) // 2
        end = start + frames * self.hop
        return wave[..., start:end] / envelope[..., start:end].clamp_min(1e-3)


class ConvNeXtBlock(nn.Module):
    def __init__(self, width, ffn, layer_scale):
        super().__init__()
        self.dwconv = nn.Conv1d(width, width, 7, padding=3, groups=width)
        self.norm = nn.LayerNorm(width)
        self.ffn = nn.Sequential(nn.Linear(width, ffn), nn.GELU(), nn.Linear(ffn, width))
        self.gamma = nn.Parameter(torch.full((width,), layer_scale))

    def forward(self, x):  # [B, C, T]
        h = self.dwconv(x).transpose(1, 2)
        return x + (self.gamma * self.ffn(self.norm(h))).transpose(1, 2)


class Vocoder(nn.Module):
    """Log mel [B, 80, T] -> waveform [B, 1, T * 256]."""

    def __init__(self, a):
        super().__init__()
        width, layers = a['vocoder_width'], a['vocoder_layers']
        self.embed = nn.Conv1d(MELS, width, 7, padding=3)
        self.norm = nn.LayerNorm(width)
        self.blocks = nn.ModuleList([ConvNeXtBlock(width, a['vocoder_ffn'], 1 / layers) for _ in range(layers)])
        self.final_norm = nn.LayerNorm(width)
        self.head = nn.Linear(width, FFT + 2)
        self.istft = InverseSTFT()

    def forward(self, mel):
        x = self.norm(self.embed(mel).transpose(1, 2)).transpose(1, 2)
        for block in self.blocks:
            x = block(x)
        h = self.head(self.final_norm(x.transpose(1, 2))).transpose(1, 2)
        log_magnitude, phase = h.chunk(2, 1)
        magnitude = torch.exp(log_magnitude).clamp(max=100)
        return self.istft(magnitude * torch.cos(phase), magnitude * torch.sin(phase))


class PeriodDiscriminator(nn.Module):
    def __init__(self, period, widths=(1, 32, 64, 128, 256)):
        super().__init__()
        self.period = period
        self.layers = nn.ModuleList([nn.Conv2d(a, b, (5, 1), (3, 1), padding=(2, 0))
                                     for a, b in zip(widths[:-1], widths[1:])])
        self.layers.append(nn.Conv2d(widths[-1], widths[-1], (5, 1), padding=(2, 0)))
        self.out = nn.Conv2d(widths[-1], 1, (3, 1), padding=(1, 0))

    def forward(self, wave):
        pad = (-wave.shape[-1]) % self.period
        if pad:
            wave = F.pad(wave, (0, pad), mode='reflect')
        x = wave.reshape(wave.shape[0], 1, -1, self.period)
        features = []
        for layer in self.layers:
            x = F.leaky_relu(layer(x), 0.1)
            features.append(x)
        x = self.out(x)
        features.append(x)
        return x, features


class ResolutionDiscriminator(nn.Module):
    def __init__(self, n_fft, channels=32):
        super().__init__()
        self.n_fft = n_fft
        self.layers = nn.ModuleList([
            nn.Conv2d(1, channels, (7, 5), (2, 2), padding=(3, 2)),
            nn.Conv2d(channels, channels, (5, 3), (2, 1), padding=(2, 1)),
            nn.Conv2d(channels, channels, (5, 3), (2, 1), padding=(2, 1)),
            nn.Conv2d(channels, channels, 3, padding=1)])
        self.out = nn.Conv2d(channels, 1, 3, padding=1)

    def forward(self, wave):
        window = torch.hann_window(self.n_fft, device=wave.device)
        x = torch.stft(wave[:, 0], self.n_fft, self.n_fft // 4, window=window,
                       center=False, return_complex=True).abs()[:, None]
        features = []
        for layer in self.layers:
            x = F.leaky_relu(layer(x), 0.1)
            features.append(x)
        x = self.out(x)
        features.append(x)
        return x, features


class Discriminators(nn.Module):
    """Training-only. Never exported or shipped."""

    def __init__(self):
        super().__init__()
        self.items = nn.ModuleList([PeriodDiscriminator(p) for p in (2, 3, 5, 7, 11)]
                                   + [ResolutionDiscriminator(n) for n in (512, 1024, 2048)])

    def forward(self, wave):
        return [d(wave) for d in self.items]


def count(module):
    return sum(p.numel() for p in module.parameters())
