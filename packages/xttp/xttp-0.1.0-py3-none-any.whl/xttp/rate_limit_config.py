"""Rate limit configuration for different platforms."""

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """
    Configuration for parsing rate limit headers.

    This class defines how to extract rate limit information from response headers.
    """

    name: str
    """Name of this configuration (e.g., 'cloudflare', 'binance')"""

    reset_headers: list[str] = field(default_factory=list)
    """Header names that contain the reset timestamp (Unix timestamp)"""

    remaining_headers: list[str] = field(default_factory=list)
    """Header names that contain remaining request count"""

    limit_headers: list[str] = field(default_factory=list)
    """Header names that contain the rate limit"""

    retry_after_headers: list[str] = field(default_factory=list)
    """Header names that contain retry delay in seconds (relative time)"""

    custom_parser: Callable[[dict], float | None] | None = None
    """Custom function to parse headers and return reset time (Unix timestamp)"""

    priority: int = 0
    """Priority when multiple configs are active (higher = checked first)"""


# Predefined configurations for common platforms

CLOUDFLARE = RateLimitConfig(
    name="cloudflare",
    reset_headers=["cf-ratelimit-reset"],
    remaining_headers=["cf-ratelimit-remaining"],
    limit_headers=["cf-ratelimit-limit"],
    priority=10,
)

GITHUB = RateLimitConfig(
    name="github",
    reset_headers=["x-ratelimit-reset"],
    remaining_headers=["x-ratelimit-remaining"],
    limit_headers=["x-ratelimit-limit"],
    priority=8,
)

TWITTER = RateLimitConfig(
    name="twitter",
    reset_headers=["x-rate-limit-reset"],
    remaining_headers=["x-rate-limit-remaining"],
    limit_headers=["x-rate-limit-limit"],
    priority=8,
)


def _binance_parser(headers: dict) -> float | None:
    """
    Custom parser for Binance rate limits.

    Binance uses weight-based rate limiting where certain operations
    consume more "weight" than others.
    """
    # Check if we're close to weight limit
    if "x-mbx-used-weight" in headers or "x-mbx-used-weight-1m" in headers:
        try:
            used_weight = int(
                headers.get("x-mbx-used-weight") or headers.get("x-mbx-used-weight-1m", "0")
            )
            # Binance typically has a limit of 1200 weight per minute
            if used_weight >= 1000:
                # If we're close to limit, back off for a minute
                return time.time() + 60.0
        except (ValueError, TypeError):
            pass

    # Check retry-after header
    if "retry-after" in headers:
        try:
            retry_after = float(headers["retry-after"])
            return time.time() + retry_after
        except (ValueError, TypeError):
            pass

    return None


BINANCE = RateLimitConfig(
    name="binance",
    retry_after_headers=["retry-after"],
    custom_parser=_binance_parser,
    priority=9,
)

STANDARD_HTTP = RateLimitConfig(
    name="standard",
    reset_headers=["x-ratelimit-reset", "ratelimit-reset"],
    remaining_headers=["x-ratelimit-remaining", "ratelimit-remaining"],
    limit_headers=["x-ratelimit-limit", "ratelimit-limit"],
    retry_after_headers=["retry-after"],
    priority=5,
)

# Default configuration set (covers most common platforms)
DEFAULT_CONFIGS = [
    CLOUDFLARE,
    BINANCE,
    GITHUB,
    TWITTER,
    STANDARD_HTTP,
]
