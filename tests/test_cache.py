import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


sys.path.insert(0, str(ROOT))
from oddmouth import cache  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
