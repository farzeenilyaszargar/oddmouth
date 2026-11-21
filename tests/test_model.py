import sys
from pathlib import Path
import json
import unittest

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oddmouth.audio import HOP, mel_spectrogram
from oddmouth.model import (AcousticModel, Discriminators, InverseSTFT, Vocoder,
                            monotonic_alignment, path_from_durations, sequence_mask)
from oddmouth.text import VOCAB_SIZE, encode, BLANK

ARCH = json.loads((ROOT / "configs/mac_training.json").read_text())["architecture"]


class ModelTest(unittest.TestCase):
    def test_inverse_stft_round_trip(self):
        x = torch.randn(2, HOP * 40) * 0.1
        padded = F.pad(x[:, None], (384, 384), mode="reflect")[:, 0]
        spec = torch.stft(padded, 1024, 256, 1024, torch.hann_window(1024), center=False, return_complex=True)
        y = InverseSTFT()(spec.real, spec.imag)[:, 0]
        self.assertLess((y - x).abs().max().item(), 1e-4)

    def test_mel_frames_match_samples(self):
        self.assertEqual(mel_spectrogram(torch.zeros(HOP * 37)).shape, (1, 80, 37))

    def test_alignment_is_monotonic_and_covers_every_token(self):
        torch.manual_seed(0)
        log_p = torch.randn(2, 6, 20)
        path = monotonic_alignment(log_p, torch.tensor([6, 4]), torch.tensor([20, 9]))
        for b, (n, t) in enumerate([(6, 20), (4, 9)]):
            self.assertTrue(torch.all(path[b, :n, :t].sum(0) == 1))
            self.assertTrue(torch.all(path[b, :n].sum(1) >= 1))
            self.assertEqual(path[b].sum().item(), t)
            tokens = path[b, :n, :t].argmax(0)
            self.assertTrue(torch.all(tokens.diff() >= 0) and torch.all(tokens.diff() <= 1))

    def test_path_from_durations(self):
        path, frames = path_from_durations(torch.tensor([[2, 1, 3]]), torch.ones(1, 3, dtype=torch.bool))
        self.assertEqual(frames.item(), 6)
        self.assertEqual(path[0].argmax(0).tolist(), [0, 0, 1, 2, 2, 2])

    def test_training_step_and_synthesis_shapes(self):
        torch.manual_seed(0)
        model = AcousticModel(ARCH, VOCAB_SIZE)
        tokens = torch.randint(3, VOCAB_SIZE, (2, 11))
        lengths, frames = torch.tensor([11, 7]), torch.tensor([40, 25])
        tokens = tokens * sequence_mask(lengths, 11)
        loss, parts = model.losses(tokens, lengths, torch.randn(2, 80, 40), frames)
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        model.eval()
        mel, out_frames = model.synthesize(tokens[:1], lengths[:1], steps=2)
        self.assertEqual(mel.shape[:2], (1, 80))
        wave = Vocoder(ARCH)(mel)
        self.assertEqual(wave.shape, (1, 1, mel.shape[-1] * HOP))
        self.assertEqual(len(Discriminators()(wave)), 8)

    def test_encode_interleaves_blanks(self):
        ids = encode("hə").tolist()
        self.assertEqual(ids[0], BLANK)
        self.assertEqual(ids[::2], [BLANK] * 3)


if __name__ == "__main__":
    unittest.main()
