"""Request builder with fluent API for HTTP requests."""

from typing import TYPE_CHECKING, Any

import httpx


if TYPE_CHECKING:
    from .client import HTTPClient


class Request:
    """
    Request builder with fluent API.

    Example:
        client = HTTPClient()
        response = await client.request().set_query_param("search", "python").set_header("User-Agent", "MyApp").get("/search")
    """

    def __init__(self, client: "HTTPClient"):
        """
        Initialize request builder.

        Args:
            client: Parent HTTP client instance
        """
        self._client = client
        self._query_params: dict[str, Any] = {}
        self._headers: dict[str, str] = {}
        self._cookies: dict[str, str] = {}
        self._json_data: Any | None = None
        self._form_data: dict[str, Any] | None = None
        self._data: Any | None = None
        self._content: bytes | None = None
        self._timeout: float | None = None
        self._follow_redirects: bool = True
        self._max_retries: int | None = None
        self._auth: tuple[str, str] | None = None

    def set_query_param(self, key: str, value: Any) -> "Request":
        """
        Set a single query parameter.

        Args:
            key: Parameter name
            value: Parameter value

        Returns:
            Self for chaining
        """
        self._query_params[key] = value
        return self

    def set_query_params(self, params: dict[str, Any]) -> "Request":
        """
        Set multiple query parameters.

        Args:
            params: Dictionary of parameters

        Returns:
            Self for chaining
        """
        self._query_params.update(params)
        return self

    def set_header(self, key: str, value: str) -> "Request":
        """
        Set a single header.

        Args:
            key: Header name
            value: Header value

        Returns:
            Self for chaining
        """
        self._headers[key] = value
        return self

    def set_headers(self, headers: dict[str, str]) -> "Request":
        """
        Set multiple headers.

        Args:
            headers: Dictionary of headers

        Returns:
            Self for chaining
        """
        self._headers.update(headers)
        return self

    def set_cookie(self, key: str, value: str) -> "Request":
        """
        Set a single cookie.

        Args:
            key: Cookie name
            value: Cookie value

        Returns:
            Self for chaining
        """
        self._cookies[key] = value
        return self

    def set_cookies(self, cookies: dict[str, str]) -> "Request":
        """
        Set multiple cookies.

        Args:
            cookies: Dictionary of cookies

        Returns:
            Self for chaining
        """
        self._cookies.update(cookies)
        return self

    def set_json(self, data: Any) -> "Request":
        """
        Set JSON body data.

        Args:
            data: Data to serialize as JSON

        Returns:
            Self for chaining
        """
        self._json_data = data
        return self

    def set_form_data(self, data: dict[str, Any]) -> "Request":
        """
        Set form data (application/x-www-form-urlencoded).

        Args:
            data: Form data

        Returns:
            Self for chaining
        """
        self._form_data = data
        return self

    def set_body(self, data: Any) -> "Request":
        """
        Set raw body data.

        Args:
            data: Raw body data (bytes or other data types)

        Returns:
            Self for chaining
        """
        # Use content for bytes to avoid deprecation warning
        if isinstance(data, bytes):
            self._content = data
        else:
            self._data = data
        return self

    def set_timeout(self, timeout: float) -> "Request":
        """
        Set request timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            Self for chaining
        """
        self._timeout = timeout
        return self

    def set_follow_redirects(self, follow: bool) -> "Request":
        """
        Set whether to follow redirects.

        Args:
            follow: Whether to follow redirects

        Returns:
            Self for chaining
        """
        self._follow_redirects = follow
        return self

    def set_max_retries(self, retries: int) -> "Request":
        """
        Set max retry attempts for this request.

        Args:
            retries: Maximum retry attempts

        Returns:
            Self for chaining
        """
        self._max_retries = retries
        return self

    def set_auth(self, username: str, password: str) -> "Request":
        """
        Set basic authentication.

        Args:
            username: Username
            password: Password

        Returns:
            Self for chaining
        """
        self._auth = (username, password)
        return self

    async def get(self, url: str) -> httpx.Response:
        """
        Execute GET request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("GET", url)

    async def post(self, url: str) -> httpx.Response:
        """
        Execute POST request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("POST", url)

    async def put(self, url: str) -> httpx.Response:
        """
        Execute PUT request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("PUT", url)

    async def patch(self, url: str) -> httpx.Response:
        """
        Execute PATCH request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("PATCH", url)

    async def delete(self, url: str) -> httpx.Response:
        """
        Execute DELETE request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("DELETE", url)

    async def head(self, url: str) -> httpx.Response:
        """
        Execute HEAD request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("HEAD", url)

    async def options(self, url: str) -> httpx.Response:
        """
        Execute OPTIONS request.

        Args:
            url: URL path or full URL

        Returns:
            HTTP response
        """
        return await self._execute("OPTIONS", url)

    async def _execute(self, method: str, url: str) -> httpx.Response:
        """
        Execute the HTTP request.

        Args:
            method: HTTP method
            url: URL path or full URL

        Returns:
            HTTP response
        """
        # Determine which body parameter to use
        body_data = None
        body_content = None
        if self._form_data:
            body_data = self._form_data
        elif self._content:
            body_content = self._content
        elif self._data:
            body_data = self._data

        return await self._client._execute_request(
            method=method,
            url=url,
            params=self._query_params,
            headers=self._headers,
            cookies=self._cookies,
            json=self._json_data,
            data=body_data,
            content=body_content,
            timeout=self._timeout,
            follow_redirects=self._follow_redirects,
            max_retries=self._max_retries,
            auth=self._auth,
        )
