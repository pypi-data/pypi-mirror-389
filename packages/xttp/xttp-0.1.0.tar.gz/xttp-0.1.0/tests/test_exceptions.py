"""Tests for exception handling."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from xttp import (
    ConnectionError,
    HTTPClient,
    HTTPClientError,
    RetryError,
    TimeoutError,
)


class TestHTTPClientError:
    """Test HTTPClientError exception."""

    async def test_http_error_4xx(self, client, httpx_mock: HTTPXMock):
        """Test HTTP 4xx errors raise HTTPClientError."""
        httpx_mock.add_response(
            url="https://api.example.com/not-found",
            method="GET",
            status_code=404,
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/not-found")

        assert exc_info.value.response is not None
        assert exc_info.value.response.status_code == 404

    async def test_http_error_401(self, client, httpx_mock: HTTPXMock):
        """Test HTTP 401 unauthorized error."""
        httpx_mock.add_response(
            url="https://api.example.com/protected",
            method="GET",
            status_code=401,
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/protected")

        assert "401" in str(exc_info.value)

    async def test_http_error_403(self, client, httpx_mock: HTTPXMock):
        """Test HTTP 403 forbidden error."""
        httpx_mock.add_response(
            url="https://api.example.com/forbidden",
            method="GET",
            status_code=403,
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/forbidden")

        assert "403" in str(exc_info.value)

    async def test_http_error_with_request_info(self, client, httpx_mock: HTTPXMock):
        """Test HTTPClientError contains request information."""
        httpx_mock.add_response(
            url="https://api.example.com/error",
            method="GET",
            status_code=400,
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/error")

        assert exc_info.value.request is not None
        assert exc_info.value.response is not None


class TestRetryError:
    """Test RetryError exception."""

    async def test_retry_error_max_retries(self, httpx_mock: HTTPXMock):
        """Test RetryError is raised when max retries exceeded."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.example.com/always-fails",
                method="GET",
                status_code=500,
            )

        with pytest.raises(RetryError) as exc_info:
            await client.get("/always-fails")

        assert "Max retries exceeded" in str(exc_info.value)
        assert exc_info.value.response is not None
        assert exc_info.value.response.status_code == 500

        await client.close()

    async def test_retry_error_contains_response(self, httpx_mock: HTTPXMock):
        """Test RetryError contains last response."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            retry_statuses=(503,),
        )

        for _ in range(2):
            httpx_mock.add_response(
                url="https://api.example.com/service-unavailable",
                method="GET",
                status_code=503,
            )

        with pytest.raises(RetryError) as exc_info:
            await client.get("/service-unavailable")

        assert exc_info.value.response.status_code == 503

        await client.close()


class TestTimeoutError:
    """Test TimeoutError exception."""

    async def test_timeout_error(self, httpx_mock: HTTPXMock):
        """Test TimeoutError is raised on timeout."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            timeout=0.001,
        )

        for _ in range(2):
            httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        with pytest.raises(TimeoutError) as exc_info:
            await client.get("/timeout")

        assert "timeout" in str(exc_info.value).lower()

        await client.close()

    async def test_timeout_error_message(self, httpx_mock: HTTPXMock):
        """Test TimeoutError has descriptive message."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            timeout=0.001,
        )

        for _ in range(3):
            httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        with pytest.raises(TimeoutError) as exc_info:
            await client.get("/timeout")

        assert "3 attempts" in str(exc_info.value)

        await client.close()


class TestConnectionError:
    """Test ConnectionError exception."""

    async def test_connection_error(self, httpx_mock: HTTPXMock):
        """Test ConnectionError is raised on connection failure."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
        )

        for _ in range(2):
            httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(ConnectionError) as exc_info:
            await client.get("/unreachable")

        assert "Connection failed" in str(exc_info.value)

        await client.close()

    async def test_connection_error_with_retries(self, httpx_mock: HTTPXMock):
        """Test ConnectionError includes retry count."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=3,
            retry_backoff_factor=0.01,
        )

        for _ in range(4):
            httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(ConnectionError) as exc_info:
            await client.get("/unreachable")

        assert "4 attempts" in str(exc_info.value)

        await client.close()


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    async def test_http_client_error_base(self, httpx_mock: HTTPXMock):
        """Test HTTPClientError is base for all HTTP errors."""
        client = HTTPClient(base_url="https://api.example.com", max_retries=0)

        httpx_mock.add_response(
            url="https://api.example.com/error",
            method="GET",
            status_code=500,
        )

        with pytest.raises(HTTPClientError):
            await client.get("/error")

        await client.close()

    async def test_retry_error_is_http_client_error(self, httpx_mock: HTTPXMock):
        """Test RetryError is subclass of HTTPClientError."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        for _ in range(2):
            httpx_mock.add_response(
                url="https://api.example.com/fail",
                method="GET",
                status_code=500,
            )

        with pytest.raises(HTTPClientError):
            await client.get("/fail")

        await client.close()

    async def test_timeout_error_is_http_client_error(self, httpx_mock: HTTPXMock):
        """Test TimeoutError is subclass of HTTPClientError."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=0,
            timeout=0.001,
        )

        httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        with pytest.raises(HTTPClientError):
            await client.get("/timeout")

        await client.close()

    async def test_connection_error_is_http_client_error(self, httpx_mock: HTTPXMock):
        """Test ConnectionError is subclass of HTTPClientError."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=0,
        )

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(HTTPClientError):
            await client.get("/unreachable")

        await client.close()


class TestExceptionDetails:
    """Test exception details and attributes."""

    async def test_exception_has_message(self, client, httpx_mock: HTTPXMock):
        """Test exceptions have descriptive messages."""
        httpx_mock.add_response(
            url="https://api.example.com/error",
            method="GET",
            status_code=400,
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/error")

        assert exc_info.value.message
        assert "400" in str(exc_info.value)

    async def test_exception_response_attribute(self, client, httpx_mock: HTTPXMock):
        """Test exceptions include response when available."""
        httpx_mock.add_response(
            url="https://api.example.com/error",
            method="GET",
            status_code=404,
            json={"error": "Not found"},
        )

        with pytest.raises(HTTPClientError) as exc_info:
            await client.get("/error")

        assert exc_info.value.response is not None
        assert exc_info.value.response.status_code == 404

    async def test_exception_without_response(self, httpx_mock: HTTPXMock):
        """Test exceptions handle missing response gracefully."""
        client = HTTPClient(base_url="https://api.example.com", max_retries=0)

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(ConnectionError) as exc_info:
            await client.get("/unreachable")

        assert exc_info.value.response is None

        await client.close()


class TestExceptionWithRequestBuilder:
    """Test exceptions work correctly with request builder."""

    async def test_builder_raises_http_error(self, client, httpx_mock: HTTPXMock):
        """Test request builder raises HTTPClientError on HTTP errors."""
        httpx_mock.add_response(
            url="https://api.example.com/error",
            method="GET",
            status_code=400,
        )

        with pytest.raises(HTTPClientError):
            await client.request().get("/error")

    async def test_builder_raises_timeout_error(self, httpx_mock: HTTPXMock):
        """Test request builder raises TimeoutError on timeout."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=0,
            timeout=0.001,
        )

        httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        with pytest.raises(TimeoutError):
            await client.request().get("/timeout")

        await client.close()

    async def test_builder_raises_retry_error(self, httpx_mock: HTTPXMock):
        """Test request builder raises RetryError when retries exhausted."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        for _ in range(2):
            httpx_mock.add_response(
                url="https://api.example.com/fail",
                method="GET",
                status_code=500,
            )

        with pytest.raises(RetryError):
            await client.request().get("/fail")

        await client.close()
