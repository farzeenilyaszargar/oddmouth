"""Cooperative cache writer for future acquisition/preprocessing; no networking.

Enforces decimal byte limits on actual bytes, including unknown-size streams.
Call this for every raw/feature/temp write in the future managed-data pipeline.
Other processes writing outside this API are not controlled by this helper.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import shutil
import tempfile


class BudgetExceeded(ValueError):
    pass


def cache_bytes(root):
    root = Path(root)
    total = 0
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ValueError("Managed cache must not contain symlinks")
        if item.is_file():
            total += item.stat().st_size
    return total


def write_bounded(chunks, destination, cache_root, *, file_limit=1_000_000_000,
                  cache_limit=1_000_000_000, reserve_bytes=5_000_000_000):
    """Atomically write one iterable of bytes; remove only own temp on failure.

    Raises before writing a chunk that would exceed a limit; never truncates a
    source into a silently incomplete valid-looking file. No automatic eviction.
    Writers using this helper serialize with flock to avoid budget races.
    """
    root = Path(cache_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = Path(destination).resolve()
    if not destination.is_relative_to(root) or destination == root:
        raise ValueError("Destination must be inside managed cache")
    if file_limit <= 0 or cache_limit <= 0 or reserve_bytes < 0:
        raise ValueError("Invalid byte budget")
    with (root / ".writer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destination.exists():
            raise FileExistsError(destination)
        used = cache_bytes(root)
        if used > cache_limit:
            raise BudgetExceeded("Existing cache exceeds budget")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        written = 0
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".partial", delete=False) as output:
                temp = Path(output.name)
                for chunk in chunks:
                    if not isinstance(chunk, bytes):
                        raise TypeError("Expected byte chunks")
                    size = len(chunk)
                    if written + size > file_limit:
                        raise BudgetExceeded("File exceeds download/preprocessing chunk cap")
                    if used + written + size > cache_limit:
                        raise BudgetExceeded("Concurrent managed cache budget exhausted")
                    if shutil.disk_usage(root).free - size < reserve_bytes:
                        raise BudgetExceeded("Minimum free disk reserve reached")
                    output.write(chunk)
                    written += size
                output.flush()
                os.fsync(output.fileno())
            temp.replace(destination)
            temp = None
            return written
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
