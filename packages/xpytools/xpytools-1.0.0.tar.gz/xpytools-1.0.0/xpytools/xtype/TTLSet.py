#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

from __future__ import annotations

import threading
from collections import OrderedDict
from time import monotonic
from typing import Optional


class TTLSet:
    """
    Thread-safe set with time-to-live (TTL) expiration and auto-sweeping.

    This behaves like a lightweight, memory-safe cache for tracking transient keys
    (such as job IDs or request IDs) that should automatically expire after a set duration.

    It uses an `OrderedDict` to maintain insertion order, and an internal RLock for
    thread-safe access. Expired keys are purged automatically every few insertions,
    and old entries are evicted when the `maxsize` limit is reached.

    Parameters
    ----------
    ttl : int, default=600
        Time-to-live in seconds for each entry.
    maxsize : int, default=512
        Maximum number of cached entries before oldest entries are evicted.
    sweep_interval : int, default=50
        Number of insertions between automatic sweeps.

    Example
    -------
    ```python
    from xpytools.types import TTLSet

    seen = TTLSet(ttl=10, maxsize=100)

    seen.add("file_1")
    "file_1" in seen  # True

    import time; time.sleep(11)
    "file_1" in seen  # False — expired automatically
    ```

    Notes
    -----
    - Uses monotonic time internally (safe against system clock changes).
    - Thread-safe (uses `threading.RLock`).
    - Designed for transient ID tracking or deduplication.
    """

    def __init__(self, ttl: int = 600, maxsize: int = 512, sweep_interval: int = 50):
        self._ttl = ttl
        self._maxsize = maxsize
        self._sweep_interval = sweep_interval
        self._insert_count = 0
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.RLock()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def add(self, key: str) -> None:
        """
        Add a key to the set, resetting its expiration timestamp.

        If the key already exists, its TTL is refreshed. A cleanup sweep is
        triggered automatically after every `sweep_interval` insertions.

        Parameters
        ----------
        key : str
            The key to store.
        """
        now = monotonic()
        with self._lock:
            self._cache[key] = now + self._ttl
            self._cache.move_to_end(key)
            self._insert_count += 1

            # Automatic sweep every N insertions
            if self._insert_count >= self._sweep_interval:
                self._insert_count = 0
                self._sweep_locked(now)

            # Enforce maxsize cap
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists and is still valid (not expired).

        If the key has expired, it is automatically removed.

        Parameters
        ----------
        key : str
            The key to xcheck.

        Returns
        -------
        bool
            True if key exists and is unexpired, False otherwise.
        """
        now = monotonic()
        with self._lock:
            expire = self._cache.get(key)
            if expire is None:
                return False
            if expire <= now:
                del self._cache[key]
                return False
            return True

    def sweep(self) -> None:
        """Manually remove all expired entries."""
        with self._lock:
            self._sweep_locked()

    def clear(self) -> None:
        """Remove all entries from the cache immediately."""
        with self._lock:
            self._cache.clear()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _sweep_locked(self, now: Optional[float] = None) -> None:
        """Internal cleanup (assumes lock already held)."""
        now = now or monotonic()
        expired = [k for k, exp in self._cache.items() if exp <= now]
        for k in expired:
            self._cache.pop(k, None)
