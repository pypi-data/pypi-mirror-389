"""Tests for rate limiting functionality."""

import asyncio
import time

from pytest_httpx import HTTPXMock

from xttp import CLOUDFLARE, GITHUB, HTTPClient, RateLimitConfig


class TestRateLimiting:
    """Test rate limiting functionality."""

    async def test_rate_limit_enforced(self, httpx_mock: HTTPXMock):
        """Test that rate limit is enforced."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=3,
            rate_limit_window=0.2,
        )

        for i in range(6):
            httpx_mock.add_response(
                url=f"https://api.example.com/item/{i}",
                method="GET",
                status_code=200,
            )

        start_time = time.time()

        for i in range(6):
            await client.get(f"/item/{i}")

        elapsed = time.time() - start_time

        assert elapsed >= 0.2

        await client.close()

    async def test_rate_limit_window(self, httpx_mock: HTTPXMock):
        """Test rate limit window sliding."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=2,
            rate_limit_window=0.15,
        )

        for i in range(4):
            httpx_mock.add_response(
                url=f"https://api.example.com/item/{i}",
                method="GET",
                status_code=200,
            )

        start_time = time.time()

        for i in range(4):
            await client.get(f"/item/{i}")

        elapsed = time.time() - start_time

        assert elapsed >= 0.15

        await client.close()

    async def test_no_rate_limit(self, httpx_mock: HTTPXMock):
        """Test that no rate limit allows fast requests."""
        client = HTTPClient(base_url="https://api.example.com")

        for i in range(5):
            httpx_mock.add_response(
                url=f"https://api.example.com/item/{i}",
                method="GET",
                status_code=200,
            )

        start_time = time.time()

        for i in range(5):
            await client.get(f"/item/{i}")

        elapsed = time.time() - start_time

        # Just verify it's faster than if there were rate limits
        # Allow for overhead from test infrastructure
        assert elapsed < 2.0

        await client.close()


class TestRateLimitHeaders:
    """Test rate limit header parsing."""

    async def test_cloudflare_headers(self, httpx_mock: HTTPXMock):
        """Test Cloudflare rate limit headers are respected."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=100,
            rate_limit_configs=[CLOUDFLARE],
        )

        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=200,
            headers={
                "cf-ratelimit-limit": "100",
                "cf-ratelimit-remaining": "0",
                "cf-ratelimit-reset": str(int(time.time()) + 2),
            },
        )

        await client.get("/data")

        await client.close()

    async def test_github_headers(self, httpx_mock: HTTPXMock):
        """Test GitHub rate limit headers are respected."""
        client = HTTPClient(
            base_url="https://api.github.com",
            rate_limit=5000,
            rate_limit_configs=[GITHUB],
        )

        httpx_mock.add_response(
            url="https://api.github.com/repos/test/repo",
            method="GET",
            status_code=200,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-reset": str(int(time.time()) + 3600),
            },
        )

        response = await client.get("/repos/test/repo")
        assert response.status_code == 200

        await client.close()

    async def test_custom_rate_limit_config(self, httpx_mock: HTTPXMock):
        """Test custom rate limit configuration."""
        custom_config = RateLimitConfig(
            name="custom-api",
            reset_headers=["x-custom-reset"],
            remaining_headers=["x-custom-remaining"],
            priority=10,
        )

        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=100,
            rate_limit_configs=[custom_config],
        )

        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=200,
            headers={
                "x-custom-reset": str(int(time.time()) + 60),
                "x-custom-remaining": "50",
            },
        )

        response = await client.get("/data")
        assert response.status_code == 200

        await client.close()


class TestRateLimiterConcurrency:
    """Test rate limiter with concurrent requests."""

    async def test_concurrent_requests_rate_limited(self, httpx_mock: HTTPXMock):
        """Test concurrent requests are rate limited."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=3,
            rate_limit_window=0.2,
        )

        for i in range(6):
            httpx_mock.add_response(
                url=f"https://api.example.com/item/{i}",
                method="GET",
                status_code=200,
            )

        start_time = time.time()

        tasks = [client.get(f"/item/{i}") for i in range(6)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        assert elapsed >= 0.2

        await client.close()


class TestRateLimiterEdgeCases:
    """Test rate limiter edge cases."""

    async def test_zero_rate_limit(self):
        """Test that zero rate limit disables rate limiting."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=None,
        )

        assert client.rate_limiter is None

        await client.close()

    async def test_rate_limiter_respects_headers_disabled(self, httpx_mock: HTTPXMock):
        """Test rate limiter can ignore headers if configured."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=100,
            respect_rate_limit_headers=False,
        )

        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=200,
            headers={
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": str(int(time.time()) + 60),
            },
        )

        response = await client.get("/data")
        assert response.status_code == 200

        await client.close()


class TestRateLimiterWithRetry:
    """Test rate limiter interaction with retry mechanism."""

    async def test_rate_limit_with_retry(self, httpx_mock: HTTPXMock):
        """Test rate limiting works correctly with retries."""
        client = HTTPClient(
            base_url="https://api.example.com",
            rate_limit=10,
            rate_limit_window=1.0,
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
            status_code=200,
        )

        response = await client.get("/unstable")
        assert response.status_code == 200

        await client.close()
