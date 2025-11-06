"""Rate limiter for HTTP requests with support for time windows and multiple platforms."""

import asyncio
import time
from collections import deque

from .rate_limit_config import DEFAULT_CONFIGS, RateLimitConfig


class RateLimiter:
    """
    Async rate limiter supporting:
    - Sliding window rate limiting
    - Multiple platform rate limit headers via RateLimitConfig
    - Manual rate limits (requests per time window)
    """

    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0,
        configs: list[RateLimitConfig] | None = None,
        respect_headers: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
            configs: List of RateLimitConfig for parsing headers (defaults to all common platforms)
            respect_headers: Whether to respect rate limit headers from servers
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.respect_headers = respect_headers

        # Use default configs if none provided, sorted by priority
        self.configs = sorted(
            configs or DEFAULT_CONFIGS,
            key=lambda c: c.priority,
            reverse=True,
        )

        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()
        self._reset_time: float | None = None

    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if necessary."""
        async with self._lock:
            now = time.time()

            # Check if we need to wait due to rate limit headers
            if self._reset_time and now < self._reset_time:
                wait_time = self._reset_time - now
                await asyncio.sleep(wait_time)
                now = time.time()

            # Remove old requests outside time window
            while self.requests and now - self.requests[0] > self.time_window:
                self.requests.popleft()

            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.max_requests:
                wait_time = self.time_window - (now - self.requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self.requests.popleft()

            # Record this request
            self.requests.append(time.time())

    def update_from_headers(self, headers: dict) -> None:
        """
        Update rate limiter based on response headers.

        Uses configured RateLimitConfig instances to parse headers
        from various platforms (Cloudflare, Binance, GitHub, etc.).

        Args:
            headers: Response headers dictionary
        """
        if not self.respect_headers:
            return

        # Normalize headers to lowercase for case-insensitive matching
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Try each config in priority order
        for config in self.configs:
            reset_time = self._parse_with_config(config, headers_lower)
            if reset_time:
                self._reset_time = reset_time
                return

    def _parse_with_config(self, config: RateLimitConfig, headers: dict) -> float | None:
        """
        Parse headers using a specific configuration.

        Args:
            config: Rate limit configuration
            headers: Normalized (lowercase) headers dictionary

        Returns:
            Reset time (Unix timestamp) or None
        """
        # 1. Try custom parser first (highest priority for this config)
        if config.custom_parser:
            try:
                reset_time = config.custom_parser(headers)
                if reset_time:
                    return reset_time
            except Exception:
                pass  # Fall through to standard parsing

        # 2. Try reset headers (Unix timestamp)
        for header_name in config.reset_headers:
            if header_name.lower() in headers:
                try:
                    return float(headers[header_name.lower()])
                except (ValueError, TypeError):
                    continue

        # 3. Try retry-after headers (relative seconds)
        for header_name in config.retry_after_headers:
            if header_name.lower() in headers:
                try:
                    retry_after = float(headers[header_name.lower()])
                    return time.time() + retry_after
                except (ValueError, TypeError):
                    continue

        # 4. Check remaining count with reset time
        remaining = None
        reset_time = None

        for header_name in config.remaining_headers:
            if header_name.lower() in headers:
                try:
                    remaining = int(headers[header_name.lower()])
                    break
                except (ValueError, TypeError):
                    continue

        # If remaining is 0, find the reset time
        if remaining == 0:
            for header_name in config.reset_headers:
                if header_name.lower() in headers:
                    try:
                        reset_time = float(headers[header_name.lower()])
                        return reset_time
                    except (ValueError, TypeError):
                        continue

        return None

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.requests.clear()
        self._reset_time = None
