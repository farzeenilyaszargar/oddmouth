import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cache = module("bounded_cache")
planner = module("plan_training")


class CacheTest(unittest.TestCase):
    def test_boundary_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(cache.write_bounded([b"123", b"45"], root / "ok", root,
                                                file_limit=5, cache_limit=6, reserve_bytes=0), 5)
            with self.assertRaises(cache.BudgetExceeded):
                cache.write_bounded([b"12"], root / "over", root,
                                    file_limit=5, cache_limit=6, reserve_bytes=0)
            self.assertFalse((root / "over").exists())
            self.assertFalse(list(root.glob("*.partial")))
            self.assertEqual((root / "ok").read_bytes(), b"12345")

    def test_unknown_length_stream_over_file_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(cache.BudgetExceeded):
                cache.write_bounded(iter([b"123", b"456"]), root / "x", root,
                                    file_limit=5, cache_limit=100, reserve_bytes=0)
            self.assertFalse((root / "x").exists())
            self.assertEqual(cache.cache_bytes(root), 0)

    def test_expansion_and_free_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "raw").write_bytes(b"1234")
            with self.assertRaises(cache.BudgetExceeded):
                cache.write_bounded([b"abc", b"def"], root / "features", root,
                                    file_limit=8, cache_limit=9, reserve_bytes=0)
            with patch.object(cache.shutil, "disk_usage") as usage:
                usage.return_value.free = 10
                with self.assertRaises(cache.BudgetExceeded):
                    cache.write_bounded([b"12"], root / "x", root,
                                        file_limit=5, cache_limit=20, reserve_bytes=9)
            self.assertEqual((root / "raw").read_bytes(), b"1234")

    def test_refuses_escape_and_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                cache.write_bounded([], root.parent / "outside", root)
            (root / "keep").write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                cache.write_bounded([], root / "keep", root)
            self.assertEqual((root / "keep").read_bytes(), b"original")

    def test_stream_failure_keeps_no_completed_file(self):
        def broken():
            yield b"first"
            raise OSError("connection dropped")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(OSError):
                cache.write_bounded(broken(), root / "x", root, reserve_bytes=0)
            self.assertFalse((root / "x").exists())
            self.assertEqual(cache.cache_bytes(root), 0)


class PlanningTest(unittest.TestCase):
    def test_all_modules_and_vocoder_fit(self):
        config = json.loads((ROOT / "configs/mac_training.json").read_text())
        counts = planner.parameter_estimate(config)
        self.assertIn("vocoder_reservation_not_counted_weights", counts)
        self.assertLessEqual(sum(counts.values()), 50_000_000)
        self.assertGreater(sum(counts.values()), 40_000_000)
        self.assertEqual(config["storage"]["max_download_chunk_bytes"], 1_000_000_000)

    def test_scratch_single_voice_without_emotion_modules(self):
        config = json.loads((ROOT / "configs/mac_training.json").read_text())
        scope = config["training_scope"]
        self.assertEqual(scope["speaker_count"], 1)
        self.assertFalse(scope["pretrained_tts_weights"])
        self.assertFalse(scope["emotion_controls"])
        self.assertFalse(scope["teacher_distillation"])
        self.assertFalse(scope["other_speaker_training_audio"])
        self.assertFalse(any("emotion" in key for key in planner.parameter_estimate(config)))
        self.assertIn("train_vocoder_from_random_init", config["training"]["stages"])

    def test_rejects_oversized_architecture_and_cache(self):
        config = json.loads((ROOT / "configs/mac_training.json").read_text())
        with patch.object(planner, "command", return_value=None):
            config["architecture_candidate"]["flow_layers"] = 100
            with self.assertRaises(ValueError):
                planner.build_report(config)
            config["architecture_candidate"]["flow_layers"] = 12
            config["storage"]["temporary_bytes"] = 1_000_000_000
            with self.assertRaises(ValueError):
                planner.build_report(config)


if __name__ == "__main__":
    unittest.main()
