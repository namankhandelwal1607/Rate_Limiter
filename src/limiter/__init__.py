from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
import time
from typing import Deque, Dict

from src.config import RateLimitConfig


class RateLimiter(ABC):
    def __init__(self, config: RateLimitConfig):
        self.config = config

    @abstractmethod
    def allow_request(self, key: str) -> bool:
        """Returns True if request is allowed, False otherwise."""
        pass

    def allowRequest(self, key: str) -> bool:
        return self.allow_request(key)


class FixedWindowRateLimiter(RateLimiter):
    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._request_counts: Dict[str, int] = {}
        self._window_start: float = time.monotonic()

    def allow_request(self, key: str) -> bool:
        now = time.monotonic()
        elapsed_seconds = int(now - self._window_start)

        if elapsed_seconds >= self.config.window_size_in_seconds:
            self._request_counts.clear()
            self._window_start = now

        count = self._request_counts.get(key, 0) + 1
        self._request_counts[key] = count

        if count > self.config.max_requests:
            return False

        return True


class SlidingWindowRateLimiter(RateLimiter):
    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._request_timestamps: Dict[str, Deque[float]] = defaultdict(deque)

    def allow_request(self, key: str) -> bool:
        now = time.monotonic()
        timestamps = self._request_timestamps[key]

        while timestamps:
            elapsed = int(now - timestamps[0])
            if elapsed >= self.config.window_size_in_seconds:
                timestamps.popleft()
            else:
                break

        if len(timestamps) >= self.config.max_requests:
            return False

        timestamps.append(now)
        return True


@dataclass
class _TokenBucketState:
    tokens: float
    last_refill: float


class TokenBucketRateLimiter(RateLimiter):
    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._buckets: Dict[str, _TokenBucketState] = {}

    def allow_request(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets.get(key)

        if bucket is None:
            bucket = _TokenBucketState(tokens=float(self.config.bucket_capacity), last_refill=now)
            self._buckets[key] = bucket

        elapsed_seconds = int(now - bucket.last_refill)
        bucket.tokens = min(
            float(self.config.bucket_capacity),
            bucket.tokens + elapsed_seconds * self.config.refill_rate_per_second,
        )
        bucket.last_refill = now

        if bucket.tokens < 1.0:
            return False

        bucket.tokens -= 1.0
        return True


@dataclass
class _LeakyBucketState:
    queued_requests: int
    last_leak: float


class LeakyBucketRateLimiter(RateLimiter):
    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self._buckets: Dict[str, _LeakyBucketState] = {}

    def allow_request(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets.get(key)

        if bucket is None:
            bucket = _LeakyBucketState(queued_requests=0, last_leak=now)
            self._buckets[key] = bucket

        elapsed_seconds = int(now - bucket.last_leak)
        leaked = elapsed_seconds * self.config.refill_rate_per_second
        bucket.queued_requests = max(0, bucket.queued_requests - leaked)
        bucket.last_leak = now

        if bucket.queued_requests >= self.config.bucket_capacity:
            return False

        bucket.queued_requests += 1
        return True
