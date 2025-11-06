"""Tests for Request builder (fluent API)."""

from pytest_httpx import HTTPXMock


class TestRequestBuilder:
    """Test Request builder fluent API."""

    async def test_create_request_builder(self, client):
        """Test creating a request builder."""
        request = client.request()
        assert request is not None
        assert request._client is client

    async def test_set_query_param(self, client, httpx_mock: HTTPXMock):
        """Test setting single query parameter."""
        httpx_mock.add_response(
            url="https://api.example.com/search?q=python",
            method="GET",
            json={"results": []},
            status_code=200,
        )

        response = await client.request().set_query_param("q", "python").get("/search")
        assert response.status_code == 200

    async def test_set_multiple_query_params(self, client, httpx_mock: HTTPXMock):
        """Test setting multiple query parameters."""
        httpx_mock.add_response(
            url="https://api.example.com/search?q=python&size=20",
            method="GET",
            json={"results": []},
            status_code=200,
        )

        response = await (
            client.request()
            .set_query_param("q", "python")
            .set_query_param("size", 20)
            .get("/search")
        )
        assert response.status_code == 200

    async def test_set_query_params_batch(self, client, httpx_mock: HTTPXMock):
        """Test setting query parameters in batch."""
        httpx_mock.add_response(
            url="https://api.example.com/search?q=python&size=20&page=1",
            method="GET",
            json={"results": []},
            status_code=200,
        )

        response = await (
            client.request().set_query_params({"q": "python", "size": 20, "page": 1}).get("/search")
        )
        assert response.status_code == 200

    async def test_set_header(self, client, httpx_mock: HTTPXMock):
        """Test setting single header."""
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            match_headers={"X-Custom": "value"},
            json={"data": "test"},
            status_code=200,
        )

        response = await client.request().set_header("X-Custom", "value").get("/data")
        assert response.status_code == 200

    async def test_set_multiple_headers(self, client, httpx_mock: HTTPXMock):
        """Test setting multiple headers."""
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            match_headers={"X-Custom-1": "value1", "X-Custom-2": "value2"},
            json={"data": "test"},
            status_code=200,
        )

        response = await (
            client.request()
            .set_header("X-Custom-1", "value1")
            .set_header("X-Custom-2", "value2")
            .get("/data")
        )
        assert response.status_code == 200

    async def test_set_headers_batch(self, client, httpx_mock: HTTPXMock):
        """Test setting headers in batch."""
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            match_headers={"X-Custom-1": "value1", "X-Custom-2": "value2"},
            json={"data": "test"},
            status_code=200,
        )

        response = await (
            client.request()
            .set_headers({"X-Custom-1": "value1", "X-Custom-2": "value2"})
            .get("/data")
        )
        assert response.status_code == 200

    async def test_set_cookie(self, client, httpx_mock: HTTPXMock):
        """Test setting single cookie."""
        httpx_mock.add_response(
            url="https://api.example.com/profile",
            method="GET",
            json={"user": "alice"},
            status_code=200,
        )

        response = await client.request().set_cookie("session", "abc123").get("/profile")
        assert response.status_code == 200

    async def test_set_cookies_batch(self, client, httpx_mock: HTTPXMock):
        """Test setting cookies in batch."""
        httpx_mock.add_response(
            url="https://api.example.com/profile",
            method="GET",
            json={"user": "alice"},
            status_code=200,
        )

        response = await (
            client.request()
            .set_cookies({"session": "abc123", "preference": "dark_mode"})
            .get("/profile")
        )
        assert response.status_code == 200

    async def test_set_json(self, client, httpx_mock: HTTPXMock):
        """Test setting JSON body."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            match_json={"name": "alice", "email": "alice@example.com"},
            json={"id": 1},
            status_code=201,
        )

        response = await (
            client.request()
            .set_json({"name": "alice", "email": "alice@example.com"})
            .post("/users")
        )
        assert response.status_code == 201

    async def test_set_form_data(self, client, httpx_mock: HTTPXMock):
        """Test setting form data."""
        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            status_code=200,
        )

        response = await (
            client.request()
            .set_form_data({"username": "alice", "password": "secret"})
            .post("/login")
        )
        assert response.status_code == 200

    async def test_set_body(self, client, httpx_mock: HTTPXMock):
        """Test setting raw body."""
        httpx_mock.add_response(
            url="https://api.example.com/upload",
            method="POST",
            status_code=201,
        )

        response = await client.request().set_body(b"raw data").post("/upload")
        assert response.status_code == 201

    async def test_set_timeout(self, client, httpx_mock: HTTPXMock):
        """Test setting request timeout."""
        httpx_mock.add_response(
            url="https://api.example.com/slow",
            method="GET",
            status_code=200,
        )

        response = await client.request().set_timeout(5.0).get("/slow")
        assert response.status_code == 200

    async def test_set_follow_redirects(self, client, httpx_mock: HTTPXMock):
        """Test setting follow_redirects."""
        httpx_mock.add_response(
            url="https://api.example.com/redirect",
            method="GET",
            status_code=200,
        )

        response = await client.request().set_follow_redirects(False).get("/redirect")
        assert response.status_code == 200

    async def test_set_max_retries(self, client, httpx_mock: HTTPXMock):
        """Test setting max retries for request."""
        httpx_mock.add_response(
            url="https://api.example.com/data",
            method="GET",
            status_code=200,
        )

        response = await client.request().set_max_retries(5).get("/data")
        assert response.status_code == 200

    async def test_set_auth(self, client, httpx_mock: HTTPXMock):
        """Test setting basic authentication."""
        httpx_mock.add_response(
            url="https://api.example.com/protected",
            method="GET",
            json={"data": "secret"},
            status_code=200,
        )

        response = await client.request().set_auth("user", "pass").get("/protected")
        assert response.status_code == 200


class TestRequestBuilderChaining:
    """Test fluent API chaining."""

    async def test_complex_request_chain(self, client, httpx_mock: HTTPXMock):
        """Test complex request with multiple chained methods."""
        httpx_mock.add_response(
            url="https://api.example.com/search?q=python&size=20",
            method="GET",
            match_headers={"User-Agent": "MyApp/1.0", "X-API-Key": "secret"},
            json={"results": []},
            status_code=200,
        )

        response = await (
            client.request()
            .set_query_param("q", "python")
            .set_query_param("size", 20)
            .set_header("User-Agent", "MyApp/1.0")
            .set_header("X-API-Key", "secret")
            .set_timeout(10.0)
            .get("/search")
        )
        assert response.status_code == 200

    async def test_post_with_json_and_headers(self, client, httpx_mock: HTTPXMock):
        """Test POST request with JSON body and headers."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            match_json={"name": "alice"},
            match_headers={"X-Request-ID": "req-123"},
            json={"id": 1},
            status_code=201,
        )

        response = await (
            client.request()
            .set_json({"name": "alice"})
            .set_header("X-Request-ID", "req-123")
            .post("/users")
        )
        assert response.status_code == 201


class TestRequestBuilderAllMethods:
    """Test all HTTP methods with request builder."""

    async def test_builder_get(self, client, httpx_mock: HTTPXMock):
        """Test GET with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            status_code=200,
        )

        response = await client.request().get("/users")
        assert response.status_code == 200

    async def test_builder_post(self, client, httpx_mock: HTTPXMock):
        """Test POST with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            status_code=201,
        )

        response = await client.request().post("/users")
        assert response.status_code == 201

    async def test_builder_put(self, client, httpx_mock: HTTPXMock):
        """Test PUT with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="PUT",
            status_code=200,
        )

        response = await client.request().put("/users/1")
        assert response.status_code == 200

    async def test_builder_patch(self, client, httpx_mock: HTTPXMock):
        """Test PATCH with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="PATCH",
            status_code=200,
        )

        response = await client.request().patch("/users/1")
        assert response.status_code == 200

    async def test_builder_delete(self, client, httpx_mock: HTTPXMock):
        """Test DELETE with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="DELETE",
            status_code=204,
        )

        response = await client.request().delete("/users/1")
        assert response.status_code == 204

    async def test_builder_head(self, client, httpx_mock: HTTPXMock):
        """Test HEAD with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="HEAD",
            status_code=200,
        )

        response = await client.request().head("/users")
        assert response.status_code == 200

    async def test_builder_options(self, client, httpx_mock: HTTPXMock):
        """Test OPTIONS with request builder."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="OPTIONS",
            status_code=200,
        )

        response = await client.request().options("/users")
        assert response.status_code == 200
