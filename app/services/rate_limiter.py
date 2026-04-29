import threading
import time
from typing import Optional


class TokenBucket:
    """Simple token bucket rate limiter.

    Refill is calculated continuously based on elapsed time so there is no
    separate background thread required.
    """

    def __init__(self, capacity: int, refill_interval_seconds: int, reserved: int = 0):
        self.capacity = float(capacity)
        self.refill_interval = float(refill_interval_seconds)
        self.refill_rate_per_sec = self.capacity / self.refill_interval
        self._tokens = float(capacity)
        self._last = time.time()
        self._lock = threading.Lock()
        self.reserved = int(reserved)

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last
        if elapsed <= 0:
            return
        add = elapsed * self.refill_rate_per_sec
        self._tokens = min(self.capacity, self._tokens + add)
        self._last = now

    def available(self) -> float:
        with self._lock:
            self._refill()
            avail = max(0.0, self._tokens - self.reserved)
            return avail

    def try_acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self._tokens - self.reserved >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire(self, tokens: int = 1, block: bool = True, timeout: Optional[float] = None) -> bool:
        if tokens <= 0:
            return True
        deadline = None if timeout is None else time.time() + timeout
        while True:
            got = self.try_acquire(tokens)
            if got:
                return True
            if not block:
                return False
            if deadline is not None and time.time() > deadline:
                return False
            # Sleep a small amount proportional to refill rate to avoid hot-looping
            time.sleep(max(0.05, 1.0 / max(1.0, self.refill_rate_per_sec)))

    def get_state(self) -> dict:
        with self._lock:
            self._refill()
            return {"tokens": float(self._tokens), "capacity": float(self.capacity), "reserved": int(self.reserved)}
