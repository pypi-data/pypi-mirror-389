"""
Modern async HTTP client with fluent API.

Example:
    from client import HTTPClient

    async with HTTPClient(base_url="https://api.example.com") as client:
        # Using fluent API
        response = await client.request().set_query_param("search", "python").get("/search")

        # Direct method calls
        response = await client.get("/users", params={"page": 1})
"""

from .client import HTTPClient
from .exceptions import (
    ConnectionError,
    HTTPClientError,
    RateLimitError,
    RetryError,
    TimeoutError,
)
from .rate_limit_config import (
    BINANCE,
    CLOUDFLARE,
    GITHUB,
    STANDARD_HTTP,
    TWITTER,
    RateLimitConfig,
)
from .rate_limiter import RateLimiter
from .request import Request


__all__ = [
    "BINANCE",
    # Predefined configs
    "CLOUDFLARE",
    "GITHUB",
    "STANDARD_HTTP",
    "TWITTER",
    "ConnectionError",
    "HTTPClient",
    "HTTPClientError",
    "RateLimitConfig",
    "RateLimitError",
    "RateLimiter",
    "Request",
    "RetryError",
    "TimeoutError",
]
