import threading
import time
from collections import deque


class AIBudget:
    """Caps how many paid AI calls the app makes in a rolling window.

    This exists because the public demo runs against a real, billed Azure
    OpenAI deployment behind a link anyone can open: per-IP rate limiting
    bounds one visitor, not the total spend. Callers that run out of budget
    are meant to degrade to the demo client rather than fail -- see
    src/analyzer/budgeted_client.py.
    """

    def __init__(self, max_calls: int, window_seconds: int = 3600, now=time.monotonic):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._now = now
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    @property
    def unlimited(self) -> bool:
        return self._max_calls <= 0

    def _forget_expired(self) -> None:
        cutoff = self._now() - self._window_seconds
        while self._calls and self._calls[0] <= cutoff:
            self._calls.popleft()

    def try_consume(self) -> bool:
        """Spend one call if the window has room. True if it was spent."""
        if self.unlimited:
            return True
        with self._lock:
            self._forget_expired()
            if len(self._calls) >= self._max_calls:
                return False
            self._calls.append(self._now())
            return True

    def is_exhausted(self) -> bool:
        if self.unlimited:
            return False
        with self._lock:
            self._forget_expired()
            return len(self._calls) >= self._max_calls
