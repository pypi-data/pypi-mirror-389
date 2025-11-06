"""Tests for retry mechanism."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from xttp import HTTPClient, RetryError, TimeoutError


class TestRetryMechanism:
    """Test automatic retry mechanism."""

    async def test_retry_on_500_error(self, httpx_mock: HTTPXMock):
        """Test retry on 500 error."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=500,
        )
        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=500,
        )
        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=200,
            json={"status": "ok"},
        )

        response = await client.get("/unstable")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        await client.close()

    async def test_retry_exhausted(self, httpx_mock: HTTPXMock):
        """Test retry exhaustion raises RetryError."""
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
        await client.close()

    async def test_retry_on_429_rate_limit(self, httpx_mock: HTTPXMock):
        """Test retry on 429 rate limit error."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            retry_statuses=(429,),
        )

        httpx_mock.add_response(
            url="https://api.example.com/limited",
            method="GET",
            status_code=429,
        )
        httpx_mock.add_response(
            url="https://api.example.com/limited",
            method="GET",
            status_code=200,
            json={"data": "success"},
        )

        response = await client.get("/limited")
        assert response.status_code == 200

        await client.close()

    async def test_retry_on_timeout(self, httpx_mock: HTTPXMock):
        """Test retry on timeout."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            timeout=0.001,
        )

        httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))
        httpx_mock.add_response(
            url="https://api.example.com/slow",
            method="GET",
            status_code=200,
        )

        response = await client.get("/slow")
        assert response.status_code == 200

        await client.close()

    async def test_retry_timeout_exhausted(self, httpx_mock: HTTPXMock):
        """Test timeout retry exhaustion."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            timeout=0.001,
        )

        for _ in range(3):
            httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        with pytest.raises(TimeoutError) as exc_info:
            await client.get("/always-timeout")

        assert "timeout after" in str(exc_info.value).lower()
        await client.close()

    async def test_retry_on_connection_error(self, httpx_mock: HTTPXMock):
        """Test retry on connection error."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
        )

        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))
        httpx_mock.add_response(
            url="https://api.example.com/unstable-connection",
            method="GET",
            status_code=200,
        )

        response = await client.get("/unstable-connection")
        assert response.status_code == 200

        await client.close()

    async def test_no_retry_on_success(self, httpx_mock: HTTPXMock):
        """Test no retry on successful response."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=3,
            retry_backoff_factor=0.01,
        )

        httpx_mock.add_response(
            url="https://api.example.com/stable",
            method="GET",
            status_code=200,
            json={"status": "ok"},
        )

        response = await client.get("/stable")
        assert response.status_code == 200

        assert len(httpx_mock.get_requests()) == 1

        await client.close()

    async def test_retry_with_custom_statuses(self, httpx_mock: HTTPXMock):
        """Test retry with custom status codes."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            retry_statuses=(503, 504),
        )

        httpx_mock.add_response(
            url="https://api.example.com/service",
            method="GET",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.example.com/service",
            method="GET",
            status_code=200,
        )

        response = await client.get("/service")
        assert response.status_code == 200

        await client.close()

    async def test_per_request_max_retries(self, httpx_mock: HTTPXMock):
        """Test per-request max_retries override."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        for _ in range(5):
            httpx_mock.add_response(
                url="https://api.example.com/unstable",
                method="GET",
                status_code=500,
            )
        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=200,
        )

        response = await client.get("/unstable", max_retries=5)
        assert response.status_code == 200

        await client.close()

    async def test_backoff_timing(self, httpx_mock: HTTPXMock):
        """Test exponential backoff timing."""
        import time

        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=3,
            retry_backoff_factor=0.1,
            retry_statuses=(500,),
        )

        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.example.com/unstable",
                method="GET",
                status_code=500,
            )
        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=200,
        )

        start_time = time.time()
        response = await client.get("/unstable")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed >= 0.1

        await client.close()


class TestRetryWithRequestBuilder:
    """Test retry with request builder."""

    async def test_retry_with_builder(self, httpx_mock: HTTPXMock):
        """Test retry mechanism works with request builder."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=2,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=500,
        )
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=200,
        )

        response = await client.request().get("/data")
        assert response.status_code == 200

        await client.close()

    async def test_builder_override_retries(self, httpx_mock: HTTPXMock):
        """Test request builder can override max_retries."""
        client = HTTPClient(
            base_url="https://api.example.com",
            max_retries=1,
            retry_backoff_factor=0.01,
            retry_statuses=(500,),
        )

        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.example.com/unstable",
                method="GET",
                status_code=500,
            )
        httpx_mock.add_response(
            url="https://api.example.com/unstable",
            method="GET",
            status_code=200,
        )

        response = await client.request().set_max_retries(3).get("/unstable")
        assert response.status_code == 200

        await client.close()
