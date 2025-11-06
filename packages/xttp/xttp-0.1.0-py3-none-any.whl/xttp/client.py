"""Async HTTP client with retry, rate limiting, and modern features."""

import asyncio
from typing import Any

import httpx
from loguru import logger

from .exceptions import ConnectionError, HTTPClientError, RetryError, TimeoutError
from .rate_limit_config import RateLimitConfig
from .rate_limiter import RateLimiter
from .request import Request


class HTTPClient:
    """
    Modern async HTTP client with:
    - Full async support using httpx
    - Automatic retry with exponential backoff
    - Rate limiting (manual and Cloudflare-aware)
    - Request/response time window tracking
    - Fluent API via Request builder
    - Comprehensive exception handling
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        retry_statuses: tuple[int, ...] = (408, 429, 500, 502, 503, 504),
        rate_limit: int | None = None,
        rate_limit_window: float = 60.0,
        rate_limit_configs: list[RateLimitConfig] | None = None,
        respect_rate_limit_headers: bool = True,
        headers: dict[str, str] | None = None,
        verify: bool = True,
        follow_redirects: bool = True,
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_factor: Exponential backoff factor
            retry_statuses: HTTP status codes to retry
            rate_limit: Max requests per time window (None = no limit)
            rate_limit_window: Time window for rate limiting in seconds
            rate_limit_configs: List of RateLimitConfig (defaults to all common platforms)
            respect_rate_limit_headers: Whether to respect rate limit headers from servers
            headers: Default headers for all requests
            verify: Whether to verify SSL certificates
            follow_redirects: Whether to follow redirects by default
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_statuses = retry_statuses
        self.default_headers = headers or {}
        self.verify = verify
        self.follow_redirects = follow_redirects

        # Initialize rate limiter if needed
        self.rate_limiter: RateLimiter | None = None
        if rate_limit:
            self.rate_limiter = RateLimiter(
                max_requests=rate_limit,
                time_window=rate_limit_window,
                configs=rate_limit_configs,
                respect_headers=respect_rate_limit_headers,
            )

        # Initialize httpx client (will be created on first use)
        self._client: httpx.AsyncClient | None = None
        self._closed = False

    async def __aenter__(self) -> "HTTPClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure httpx client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self.default_headers,
                verify=self.verify,
                follow_redirects=self.follow_redirects,
            )

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client and not self._closed:
            await self._client.aclose()
            self._closed = True
            logger.debug("HTTP client closed")

    def request(self) -> Request:
        """
        Create a new request builder.

        Returns:
            Request builder instance

        Example:
            response = await client.request().set_query_param("search", "python").get("/search")
        """
        return Request(self)

    async def _execute_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        content: bytes | None = None,
        timeout: float | None = None,
        follow_redirects: bool | None = None,
        max_retries: int | None = None,
        auth: tuple[str, str] | None = None,
    ) -> httpx.Response:
        """
        Execute HTTP request with retry and rate limiting.

        Args:
            method: HTTP method
            url: URL path or full URL
            params: Query parameters
            headers: Request headers
            cookies: Request cookies
            json: JSON data
            data: Form data or non-bytes body
            content: Raw bytes content
            timeout: Request timeout
            follow_redirects: Whether to follow redirects
            max_retries: Max retry attempts (overrides client default)
            auth: Basic auth tuple (username, password)

        Returns:
            HTTP response

        Raises:
            HTTPClientError: On request failure
            RetryError: When all retries exhausted
            TimeoutError: On timeout
            ConnectionError: On connection failure
        """
        await self._ensure_client()
        assert self._client is not None

        # Build full URL
        if not url.startswith(("http://", "https://")):
            url = f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"

        # Use provided retries or default
        retries = max_retries if max_retries is not None else self.max_retries

        # Attempt request with retries
        for attempt in range(retries + 1):
            try:
                # Acquire rate limit permission
                if self.rate_limiter:
                    await self.rate_limiter.acquire()

                # Execute request
                logger.debug(f"[Attempt {attempt + 1}/{retries + 1}] {method} {url}")

                # Merge cookies into headers to avoid deprecation warning
                request_headers = headers.copy() if headers else {}
                if cookies:
                    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                    if "cookie" in request_headers or "Cookie" in request_headers:
                        existing = request_headers.get("cookie") or request_headers.get("Cookie")
                        request_headers["Cookie"] = f"{existing}; {cookie_str}"
                    else:
                        request_headers["Cookie"] = cookie_str

                # Use content parameter for raw bytes to avoid deprecation warning
                # Call directly instead of using dict unpacking to satisfy type checker
                if content is not None:
                    response = await self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=request_headers,
                        json=json,
                        content=content,
                        timeout=timeout or self.timeout,
                        follow_redirects=(
                            follow_redirects
                            if follow_redirects is not None
                            else self.follow_redirects
                        ),
                        auth=auth,
                    )
                elif data is not None:
                    response = await self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=request_headers,
                        json=json,
                        data=data,
                        timeout=timeout or self.timeout,
                        follow_redirects=(
                            follow_redirects
                            if follow_redirects is not None
                            else self.follow_redirects
                        ),
                        auth=auth,
                    )
                else:
                    response = await self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=request_headers,
                        json=json,
                        timeout=timeout or self.timeout,
                        follow_redirects=(
                            follow_redirects
                            if follow_redirects is not None
                            else self.follow_redirects
                        ),
                        auth=auth,
                    )

                # Update rate limiter from response headers
                if self.rate_limiter:
                    self.rate_limiter.update_from_headers(dict(response.headers))

                # Check if we should retry based on status code
                if response.status_code in self.retry_statuses:
                    if attempt < retries:
                        wait_time = self.retry_backoff_factor**attempt
                        logger.warning(
                            f"Request failed with status {response.status_code}, "
                            f"retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise RetryError(
                            f"Max retries exceeded. Last status: {response.status_code}",
                            response=response,
                        )

                # Raise for other error status codes
                response.raise_for_status()

                logger.debug(f"Request successful: {method} {url} -> {response.status_code}")
                return response

            except httpx.TimeoutException as e:
                if attempt < retries:
                    wait_time = self.retry_backoff_factor**attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise TimeoutError(f"Request timeout after {retries + 1} attempts") from e

            except httpx.ConnectError as e:
                if attempt < retries:
                    wait_time = self.retry_backoff_factor**attempt
                    logger.warning(f"Connection failed, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ConnectionError(f"Connection failed after {retries + 1} attempts") from e

            except httpx.HTTPStatusError as e:
                if attempt < retries and e.response.status_code in self.retry_statuses:
                    wait_time = self.retry_backoff_factor**attempt
                    logger.warning(
                        f"HTTP error {e.response.status_code}, retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise HTTPClientError(
                        f"HTTP error: {e.response.status_code}",
                        response=e.response,
                        request=e.request,
                    ) from e

            except (RetryError, TimeoutError, ConnectionError):
                raise

            except Exception as e:
                raise HTTPClientError(f"Unexpected error: {e!s}") from e

        # Should never reach here, but just in case
        raise RetryError("Max retries exceeded")

    # Convenience methods for direct usage (without Request builder)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Execute GET request."""
        return await self._execute_request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Execute POST request."""
        return await self._execute_request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Execute PUT request."""
        return await self._execute_request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Execute PATCH request."""
        return await self._execute_request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Execute DELETE request."""
        return await self._execute_request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> httpx.Response:
        """Execute HEAD request."""
        return await self._execute_request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs) -> httpx.Response:
        """Execute OPTIONS request."""
        return await self._execute_request("OPTIONS", url, **kwargs)
