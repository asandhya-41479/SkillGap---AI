"""Login rate limit: blocks password guessing.

After MAX_FAILED wrong passwords for one email within WINDOW_SECONDS, that email cannot log
in until the oldest failure is older than the window. A successful login clears the count.

Kept in memory: simple and enough for this deployment (Render runs one worker process).
Limitations, stated honestly: the counts reset when the server restarts, and several server
processes would each keep their own counts (a shared store such as Redis would fix both).
The key is the email even when no such account exists, so the response never reveals
whether an email is registered.
"""
import threading
import time
from collections import deque

MAX_FAILED = 5
WINDOW_SECONDS = 15 * 60


class LoginLimiter:
    def __init__(self, max_failed: int = MAX_FAILED, window_seconds: int = WINDOW_SECONDS, clock=time.monotonic):
        self.max_failed, self.window, self.clock = max_failed, window_seconds, clock
        self._failures: dict[str, deque] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def _prune(self, key: str, now: float) -> deque:
        q = self._failures.get(key, deque())
        while q and now - q[0] >= self.window:
            q.popleft()
        if q:
            self._failures[key] = q
        else:
            self._failures.pop(key, None)
        return q

    def retry_after(self, email: str) -> int:
        """Seconds until this email may try again; 0 when it is allowed now."""
        key, now = self._key(email), self.clock()
        with self._lock:
            q = self._prune(key, now)
            if len(q) < self.max_failed:
                return 0
            return max(1, int(self.window - (now - q[0])) + 1)

    def record_failure(self, email: str) -> None:
        key, now = self._key(email), self.clock()
        with self._lock:
            q = self._prune(key, now)
            q.append(now)
            self._failures[key] = q

    def reset(self, email: str) -> None:
        with self._lock:
            self._failures.pop(self._key(email), None)


login_limiter = LoginLimiter()
