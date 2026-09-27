"""Execution timing utility."""

import contextlib
import time


@contextlib.contextmanager
def timer(label: str):
    """Context manager to time code execution blocks."""
    start = time.perf_counter()
    yield
    print(f"[timer] {label}: {(time.perf_counter() - start) * 1000:.1f} ms")
