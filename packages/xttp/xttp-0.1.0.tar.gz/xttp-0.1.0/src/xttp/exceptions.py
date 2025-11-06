"""Custom exceptions for HTTP client."""

import httpx


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""

    def __init__(
        self,
        message: str,
        response: httpx.Response | None = None,
        request: httpx.Request | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.response = response
        self.request = request


class RetryError(HTTPClientError):
    """Raised when all retry attempts are exhausted."""

    pass


class RateLimitError(HTTPClientError):
    """Raised when rate limit is exceeded."""

    pass


class TimeoutError(HTTPClientError):
    """Raised when request times out."""

    pass


class ConnectionError(HTTPClientError):
    """Raised when connection fails."""

    pass
