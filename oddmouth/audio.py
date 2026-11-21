"""One shared audio convention for the acoustic model and vocoder.

22.05 kHz mono, 80 HTK mel bins up to 8 kHz, FFT 1024, hop 256, natural-log
magnitude mel with a 1e-5 floor. A clip of L samples (L a multiple of 256)
maps to exactly L / 256 mel frames, so mel frames and waveform samples align.
"""
import io
import math

import numpy as np
import torch
import torch.nn.functional as F

SR, HOP, FFT, MELS, FMAX = 22050, 256, 1024, 80, 8000
_BASIS = {}


def decode_audio(data):
    """Decode WAV/FLAC bytes to mono float32 at SR."""
    import soundfile
    from scipy.signal import resample_poly
    x, sr = soundfile.read(io.BytesIO(data), dtype='float32', always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return np.clip(x, -1, 1)


def trim_silence(x, top_db=40.0, margin_frames=4):
    """Trim leading/trailing frames quieter than peak - top_db; keep a margin."""
    frames = len(x) // HOP
    if frames < 2:
        return x
    rms = np.sqrt(np.square(x[:frames * HOP].reshape(frames, HOP)).mean(1) + 1e-12)
    db = 20 * np.log10(rms)
    voiced = np.flatnonzero(db > db.max() - top_db)
    start = max(0, voiced[0] - margin_frames)
    end = min(frames, voiced[-1] + 1 + margin_frames)
    return x[start * HOP:end * HOP]


def mel_basis(device):
    key = str(device)
    if key not in _BASIS:
        high = 2595 * math.log10(1 + FMAX / 700)
        hz = 700 * (10 ** (torch.linspace(0., high, MELS + 2) / 2595) - 1)
        freqs = torch.linspace(0, SR / 2, FFT // 2 + 1)
        left = (freqs[None] - hz[:-2, None]) / (hz[1:-1, None] - hz[:-2, None])
        right = (hz[2:, None] - freqs[None]) / (hz[2:, None] - hz[1:-1, None])
        _BASIS[key] = torch.minimum(left, right).clamp_min(0).to(device)
    return _BASIS[key]


def mel_spectrogram(wave):
    """wave [L] or [B, L] -> log mel [B, 80, L // 256]. Works on CPU and MPS."""
    if wave.ndim == 1:
        wave = wave[None]
    pad = (FFT - HOP) // 2
    padded = F.pad(wave[:, None], (pad, pad), mode='reflect')[:, 0]
    window = torch.hann_window(FFT, device=wave.device)
    spec = torch.stft(padded, FFT, HOP, FFT, window, center=False, return_complex=True).abs()
    return torch.log((mel_basis(wave.device) @ spec).clamp_min(1e-5))


def median_f0(x, max_frames=2000):
    """Rough autocorrelation F0 (Hz) over voiced frames; a data diagnostic only."""
    frames = min(len(x) // HOP - 4, max_frames)
    if frames < 1:
        return None
    chunks = np.lib.stride_tricks.sliding_window_view(x, FFT)[::HOP][:frames]
    chunks = (chunks - chunks.mean(1, keepdims=True)) * np.hanning(FFT)
    spec = np.fft.rfft(chunks, n=2 * FFT)
    corr = np.fft.irfft(np.abs(spec) ** 2, n=2 * FFT)[:, :FFT]
    lo, hi = SR // 400, SR // 60
    lag = corr[:, lo:hi].argmax(1) + lo
    strength = corr[np.arange(len(lag)), lag] / np.maximum(corr[:, 0], 1e-9)
    loud = corr[:, 0] > np.percentile(corr[:, 0], 30)
    voiced = (strength > 0.6) & loud
    return float(np.median(SR / lag[voiced])) if voiced.any() else None
