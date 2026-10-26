"""
Polling helper for state that settles asynchronously (UI catching up with the backend).
"""
from __future__ import annotations

from collections.abc import Callable
import time
from typing import TypeVar

T = TypeVar("T")


def wait_until(probe: Callable[[], T], done: Callable[[T], bool], timeout_s: float = 30.0,
               interval_s: float = 1.0) -> T:
    """
    Calls `probe` until `done(result)` is true or the timeout passes; returns the last result
    either way so the caller can assert on it with a meaningful message.
    """
    deadline = time.monotonic() + timeout_s
    while True:
        result = probe()
        if done(result) or time.monotonic() >= deadline:
            return result
        time.sleep(interval_s)
