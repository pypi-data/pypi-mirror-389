"""Tests for HTTPClient basic functionality."""

from pytest_httpx import HTTPXMock

from xttp import HTTPClient


class TestHTTPClientBasics:
    """Test basic HTTP client functionality."""

    async def test_client_context_manager(self, base_url):
        """Test client can be used as async context manager."""
        async with HTTPClient(base_url=base_url) as client:
            assert client is not None
            assert not client._closed

        assert client._closed

    async def test_client_initialization(self, base_url):
        """Test client initialization with various parameters."""
        client = HTTPClient(
            base_url=base_url,
            timeout=60.0,
            max_retries=5,
            retry_backoff_factor=3.0,
            headers={"X-Custom": "header"},
        )

        assert client.base_url == base_url
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.retry_backoff_factor == 3.0
        assert client.default_headers == {"X-Custom": "header"}

        await client.close()

    async def test_base_url_stripping(self):
        """Test that base_url trailing slash is stripped."""
        client = HTTPClient(base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com"
        await client.close()


class TestHTTPMethods:
    """Test HTTP methods."""

    async def test_get_request(self, client, httpx_mock: HTTPXMock):
        """Test GET request."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            json={"users": ["alice", "bob"]},
            status_code=200,
        )

        response = await client.get("/users")
        assert response.status_code == 200
        assert response.json() == {"users": ["alice", "bob"]}

    async def test_post_request(self, client, httpx_mock: HTTPXMock):
        """Test POST request."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            json={"id": 123, "name": "alice"},
            status_code=201,
        )

        response = await client.post("/users", json={"name": "alice"})
        assert response.status_code == 201
        assert response.json() == {"id": 123, "name": "alice"}

    async def test_put_request(self, client, httpx_mock: HTTPXMock):
        """Test PUT request."""
        httpx_mock.add_response(
            url="https://api.example.com/users/123",
            method="PUT",
            json={"id": 123, "name": "alice updated"},
            status_code=200,
        )

        response = await client.put("/users/123", json={"name": "alice updated"})
        assert response.status_code == 200

    async def test_patch_request(self, client, httpx_mock: HTTPXMock):
        """Test PATCH request."""
        httpx_mock.add_response(
            url="https://api.example.com/users/123",
            method="PATCH",
            json={"id": 123, "name": "alice patched"},
            status_code=200,
        )

        response = await client.patch("/users/123", json={"name": "alice patched"})
        assert response.status_code == 200

    async def test_delete_request(self, client, httpx_mock: HTTPXMock):
        """Test DELETE request."""
        httpx_mock.add_response(
            url="https://api.example.com/users/123",
            method="DELETE",
            status_code=204,
        )

        response = await client.delete("/users/123")
        assert response.status_code == 204

    async def test_head_request(self, client, httpx_mock: HTTPXMock):
        """Test HEAD request."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="HEAD",
            status_code=200,
        )

        response = await client.head("/users")
        assert response.status_code == 200

    async def test_options_request(self, client, httpx_mock: HTTPXMock):
        """Test OPTIONS request."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="OPTIONS",
            status_code=200,
            headers={"Allow": "GET, POST, OPTIONS"},
        )

        response = await client.options("/users")
        assert response.status_code == 200
        assert "Allow" in response.headers


class TestRequestParameters:
    """Test request parameters."""

    async def test_query_params(self, client, httpx_mock: HTTPXMock):
        """Test request with query parameters."""
        httpx_mock.add_response(
            url="https://api.example.com/search?q=python&size=20",
            method="GET",
            json={"results": []},
            status_code=200,
        )

        response = await client.get("/search", params={"q": "python", "size": 20})
        assert response.status_code == 200

    async def test_headers(self, client, httpx_mock: HTTPXMock):
        """Test request with custom headers."""
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            match_headers={"X-Custom-Header": "test-value"},
            json={"data": "test"},
            status_code=200,
        )

        response = await client.get("/data", headers={"X-Custom-Header": "test-value"})
        assert response.status_code == 200

    async def test_cookies(self, client, httpx_mock: HTTPXMock):
        """Test request with cookies."""
        httpx_mock.add_response(
            url="https://api.example.com/profile",
            method="GET",
            json={"user": "alice"},
            status_code=200,
        )

        response = await client.get("/profile", cookies={"session": "abc123"})
        assert response.status_code == 200

    async def test_json_body(self, client, httpx_mock: HTTPXMock):
        """Test POST request with JSON body."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            match_json={"name": "alice", "email": "alice@example.com"},
            json={"id": 1},
            status_code=201,
        )

        response = await client.post("/users", json={"name": "alice", "email": "alice@example.com"})
        assert response.status_code == 201

    async def test_form_data(self, client, httpx_mock: HTTPXMock):
        """Test POST request with form data."""
        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            status_code=200,
        )

        response = await client.post("/login", data={"username": "alice", "password": "secret"})
        assert response.status_code == 200

    async def test_basic_auth(self, client, httpx_mock: HTTPXMock):
        """Test request with basic authentication."""
        httpx_mock.add_response(
            url="https://api.example.com/protected",
            method="GET",
            json={"data": "secret"},
            status_code=200,
        )

        response = await client.get("/protected", auth=("user", "pass"))
        assert response.status_code == 200


class TestURLHandling:
    """Test URL handling."""

    async def test_relative_url(self, client, httpx_mock: HTTPXMock):
        """Test relative URL is combined with base_url."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            status_code=200,
        )

        response = await client.get("/users")
        assert response.status_code == 200

    async def test_absolute_url(self, client, httpx_mock: HTTPXMock):
        """Test absolute URL overrides base_url."""
        httpx_mock.add_response(
            url="https://other-api.example.com/data",
            method="GET",
            status_code=200,
        )

        response = await client.get("https://other-api.example.com/data")
        assert response.status_code == 200

    async def test_url_without_leading_slash(self, client, httpx_mock: HTTPXMock):
        """Test URL without leading slash is handled correctly."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            status_code=200,
        )

        response = await client.get("users")
        assert response.status_code == 200


class TestTimeout:
    """Test timeout handling."""

    async def test_default_timeout(self):
        """Test client uses default timeout."""
        client = HTTPClient(timeout=10.0)
        assert client.timeout == 10.0
        await client.close()

    async def test_per_request_timeout(self, client, httpx_mock: HTTPXMock):
        """Test per-request timeout override."""
        httpx_mock.add_response(
            url="https://api.example.com/slow",
            method="GET",
            status_code=200,
        )

        response = await client.get("/slow", timeout=5.0)
        assert response.status_code == 200
