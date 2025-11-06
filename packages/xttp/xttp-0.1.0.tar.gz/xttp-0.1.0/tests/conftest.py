"""Pytest configuration and fixtures for xttp tests."""

import pytest

from xttp import HTTPClient


@pytest.fixture
def base_url():
    """Base URL for test client."""
    return "https://api.example.com"


@pytest.fixture
async def client(base_url, httpx_mock):
    """Create HTTP client for testing."""
    async with HTTPClient(base_url=base_url) as c:
        yield c


@pytest.fixture
async def client_with_retry(base_url, httpx_mock):
    """Create HTTP client with retry configuration."""
    async with HTTPClient(
        base_url=base_url,
        max_retries=3,
        retry_backoff_factor=0.1,
        retry_statuses=(408, 429, 500, 502, 503, 504),
    ) as c:
        yield c


@pytest.fixture
async def client_with_rate_limit(base_url, httpx_mock):
    """Create HTTP client with rate limiting."""
    async with HTTPClient(
        base_url=base_url,
        rate_limit=10,
        rate_limit_window=1.0,
    ) as c:
        yield c
