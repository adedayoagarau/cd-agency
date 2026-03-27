"""In-memory rate limiter with per-minute and per-hour windows."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Base rate limiter configuration.

    Parameters
    ----------
    requests_per_minute:
        Maximum requests allowed in a 60-second sliding window.
    requests_per_hour:
        Maximum requests allowed in a 3600-second sliding window.
    """

    requests_per_minute: int = 60
    requests_per_hour: int = 1000

    def check(self, key: str) -> tuple[bool, dict[str, str]]:
        """Check whether *key* is allowed to make a request.

        Returns
        -------
        tuple
            ``(allowed, headers)`` where *headers* is a dict of
            ``X-RateLimit-*`` response headers.
        """
        raise NotImplementedError

    def _build_headers(
        self,
        remaining_minute: int,
        remaining_hour: int,
        reset_seconds: int,
    ) -> dict[str, str]:
        return {
            "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(max(remaining_minute, 0)),
            "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(max(remaining_hour, 0)),
            "X-RateLimit-Reset": str(reset_seconds),
        }


@dataclass
class InMemoryRateLimiter(RateLimiter):
    """Rate limiter backed by a plain ``dict``.

    Suitable for single-process deployments or development.  For
    multi-process / multi-node setups, swap in a Redis-backed
    implementation.
    """

    _requests: dict[str, list[float]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, key: str) -> tuple[bool, dict[str, str]]:
        now = time.time()
        self._cleanup(key, now)

        timestamps = self._requests.setdefault(key, [])

        minute_ago = now - 60
        hour_ago = now - 3600

        count_minute = sum(1 for ts in timestamps if ts > minute_ago)
        count_hour = sum(1 for ts in timestamps if ts > hour_ago)

        remaining_minute = self.requests_per_minute - count_minute
        remaining_hour = self.requests_per_hour - count_hour

        allowed = remaining_minute > 0 and remaining_hour > 0

        if allowed:
            timestamps.append(now)
            remaining_minute -= 1
            remaining_hour -= 1

        # Seconds until the oldest relevant entry expires
        reset = 0
        if timestamps:
            oldest_in_minute = [ts for ts in timestamps if ts > minute_ago]
            if oldest_in_minute:
                reset = int(oldest_in_minute[0] - minute_ago)

        headers = self._build_headers(remaining_minute, remaining_hour, reset)
        return allowed, headers

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cleanup(self, key: str, now: float) -> None:
        """Remove entries older than one hour for *key*."""
        if key not in self._requests:
            return
        cutoff = now - 3600
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
