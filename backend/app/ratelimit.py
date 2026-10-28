"""In-memory limits on live analyses, which are the only requests that cost money.

A per-visitor hourly limit stops one person from draining the budget, and a
global daily cap bounds total spend for a public demo. State lives in this
process, which suits a single-instance deployment; a multi-instance setup
would move it to a shared store.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

HOUR = 3600
DAY = 86400


class RateLimiter:
    def __init__(self, per_visitor_per_hour: int, global_per_day: int, clock: Callable[[], float] = time.monotonic):
        self.per_visitor_per_hour = per_visitor_per_hour
        self.global_per_day = global_per_day
        self._clock = clock
        self._by_visitor: dict[str, deque[float]] = defaultdict(deque)
        self._all: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self, visitor: str) -> str | None:
        """Record an attempt. Returns which limit was hit, or None if allowed."""
        now = self._clock()
        with self._lock:
            _expire(self._all, now - DAY)
            mine = self._by_visitor[visitor]
            _expire(mine, now - HOUR)
            if len(self._all) >= self.global_per_day:
                return "daily"
            if len(mine) >= self.per_visitor_per_hour:
                return "visitor"
            mine.append(now)
            self._all.append(now)
            return None


def _expire(window: deque[float], cutoff: float) -> None:
    while window and window[0] <= cutoff:
        window.popleft()
