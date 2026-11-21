"""Keep Oddmouth's CPU use near a fixed share of the whole machine.

The user asked that jobs use at most 20-30% of the CPU. CpuLimiter compares
this process's CPU time with wall-clock time over a rolling window and sleeps
when usage exceeds the share. limit_threads() also caps compute threads.
"""
import os
import time

import torch


def limit_threads(share):
    threads = max(1, int((os.cpu_count() or 4) * share))
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    return threads


class CpuLimiter:
    def __init__(self, share, window_seconds=10.0):
        self.share = share
        self.cores = os.cpu_count() or 4
        self.window = window_seconds
        self._reset()

    def _reset(self):
        self.wall0, self.cpu0 = time.monotonic(), time.process_time()

    def __call__(self):
        if not self.share or self.share >= 1:
            return
        cpu = time.process_time() - self.cpu0
        wall = time.monotonic() - self.wall0
        needed = cpu / (self.share * self.cores)
        if needed > wall:
            time.sleep(needed - wall)
        if time.monotonic() - self.wall0 > self.window:
            self._reset()
