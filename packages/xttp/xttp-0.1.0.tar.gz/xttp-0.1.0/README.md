# xttp

A modern, production-ready async HTTP client for Python with fluent API, automatic retries, and intelligent rate limiting.

## Features

- **Fully Async**: Built on `httpx` for high-performance async I/O
- **Fluent API**: Pythonic builder pattern for easy request construction
- **Automatic Retry**: Exponential backoff with configurable retry strategies
- **Smart Rate Limiting**: Unified configuration system supporting multiple platforms
  - Built-in support: Cloudflare, GitHub, Twitter, Binance, Standard HTTP
  - Custom headers: Define your own rate limit headers
  - Custom parser: Write custom logic for complex rate limiting
  - Priority-based: Multiple configs checked in priority order
- **Comprehensive Error Handling**: Custom exceptions for different error types
- **Sliding Window Rate Limiting**: Time window control for request throttling
- **Context Manager Support**: Proper resource cleanup with async context managers
- **Type Safe**: Full type hints for better IDE support
- **Well Tested**: Comprehensive test suite with 88+ tests

## Installation

```bash
# Using uv (recommended)
uv add xttp

# Using pip
pip install xttp
```

## Quick Start

### Basic Usage

```python
import asyncio
from xttp import HTTPClient

async def main():
    async with HTTPClient(base_url="https://api.example.com") as client:
        # Simple GET request
        response = await client.get("/users")
        print(response.json())

asyncio.run(main())
```

### Fluent API (Recommended)

The fluent API provides a clean, chainable interface:

```python
async with HTTPClient(base_url="https://api.example.com") as client:
    response = await (
        client.request()
        .set_query_param("search", "python")
        .set_query_param("size", "large")
        .set_header("User-Agent", "MyApp/1.0")
        .get("/search")
    )
```

## Advanced Usage

### Rate Limiting

```python
# Limit to 100 requests per minute
# Automatically respects rate limit headers from all common platforms
async with HTTPClient(
    base_url="https://api.example.com",
    rate_limit=100,
    rate_limit_window=60.0,
) as client:
    for i in range(200):
        # Automatically rate limited
        response = await client.get(f"/item/{i}")
```

### Custom Rate Limit Headers

```python
from xttp import HTTPClient, RateLimitConfig

# Define custom rate limit headers for your API
custom_config = RateLimitConfig(
    name="my-api",
    reset_headers=["x-custom-reset"],
    remaining_headers=["x-custom-remaining"],
    priority=10,
)

async with HTTPClient(
    base_url="https://api.example.com",
    rate_limit=100,
    rate_limit_configs=[custom_config],
) as client:
    response = await client.get("/data")
```

### Retry Configuration

```python
async with HTTPClient(
    base_url="https://api.example.com",
    max_retries=3,
    retry_backoff_factor=2.0,  # Wait 1s, 2s, 4s between retries
    retry_statuses=(408, 429, 500, 502, 503, 504),
) as client:
    response = await client.get("/unstable-endpoint")
```

### Authentication

```python
# Basic auth
response = await (
    client.request()
    .set_auth("username", "password")
    .get("/protected")
)
```

### POST with JSON

```python
data = {
    "name": "Alice",
    "email": "alice@example.com"
}

response = await client.request().set_json(data).post("/users")
```

### Custom Headers

```python
# Client-level headers (applied to all requests)
async with HTTPClient(
    base_url="https://api.example.com",
    headers={"X-API-Key": "secret123"}
) as client:
    # Request-level headers (merged with client headers)
    response = await (
        client.request()
        .set_header("X-Request-ID", "req-001")
        .get("/data")
    )
```

### Working with Cookies

```python
response = await (
    client.request()
    .set_cookie("session_id", "abc123")
    .set_cookies({"user_pref": "dark_mode"})
    .get("/profile")
)
```

### Timeout Control

```python
# Per-request timeout
response = await client.request().set_timeout(5.0).get("/slow-endpoint")

# Client-level default timeout
async with HTTPClient(timeout=10.0) as client:
    response = await client.get("/endpoint")
```

### Query Parameters

```python
# Multiple ways to set query parameters

# Method 1: Fluent API
response = await (
    client.request()
    .set_query_param("page", "1")
    .set_query_param("size", "20")
    .get("/items")
)

# Method 2: Batch set
response = await (
    client.request()
    .set_query_params({"page": "1", "size": "20"})
    .get("/items")
)

# Method 3: Direct method
response = await client.get("/items", params={"page": "1", "size": "20"})
```

## Error Handling

```python
from xttp import (
    HTTPClientError,
    RetryError,
    TimeoutError,
    ConnectionError,
)

async with HTTPClient(base_url="https://api.example.com") as client:
    try:
        response = await client.get("/endpoint")
        response.raise_for_status()
    except RetryError as e:
        print(f"All retries exhausted: {e.message}")
    except TimeoutError as e:
        print(f"Request timed out: {e.message}")
    except ConnectionError as e:
        print(f"Connection failed: {e.message}")
    except HTTPClientError as e:
        print(f"HTTP error: {e.message}")
        if e.response:
            print(f"Status: {e.response.status_code}")
```

## Platform-Specific Examples

### Binance API

```python
from xttp import HTTPClient, BINANCE

async with HTTPClient(
    base_url="https://api.binance.com",
    rate_limit=1200,  # Binance weight limit
    rate_limit_window=60.0,
    rate_limit_configs=[BINANCE],  # Use Binance-specific config
) as client:
    # Automatically respects X-MBX-USED-WEIGHT headers
    response = await client.get("/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
```

### GitHub API

```python
from xttp import HTTPClient, GITHUB

async with HTTPClient(
    base_url="https://api.github.com",
    headers={"Accept": "application/vnd.github.v3+json"},
    rate_limit=5000,  # GitHub's rate limit
    rate_limit_configs=[GITHUB],  # Use GitHub-specific config
) as client:
    # Automatically respects X-RateLimit-* headers
    response = await client.get("/repos/python/cpython")
```

### Multiple Platforms

```python
from xttp import HTTPClient, CLOUDFLARE, GITHUB, BINANCE

# Support multiple platforms simultaneously
async with HTTPClient(
    base_url="https://api.example.com",
    rate_limit=100,
    rate_limit_configs=[CLOUDFLARE, GITHUB, BINANCE],
) as client:
    # Client will automatically detect and respect headers from any of these platforms
    response = await client.get("/data")
```

## API Reference

### HTTPClient

**Constructor Parameters:**
- `base_url`: Base URL for all requests
- `timeout`: Default timeout in seconds (default: 30.0)
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_backoff_factor`: Exponential backoff factor (default: 2.0)
- `retry_statuses`: HTTP status codes to retry (default: (408, 429, 500, 502, 503, 504))
- `rate_limit`: Max requests per time window (default: None)
- `rate_limit_window`: Time window for rate limiting in seconds (default: 60.0)
- `rate_limit_configs`: List of RateLimitConfig instances (default: all common platforms)
- `respect_rate_limit_headers`: Whether to respect rate limit headers from servers (default: True)
- `headers`: Default headers for all requests
- `verify`: Whether to verify SSL certificates (default: True)
- `follow_redirects`: Whether to follow redirects (default: True)

**Methods:**
- `request()`: Create a new Request builder
- `get(url, **kwargs)`: Execute GET request
- `post(url, **kwargs)`: Execute POST request
- `put(url, **kwargs)`: Execute PUT request
- `patch(url, **kwargs)`: Execute PATCH request
- `delete(url, **kwargs)`: Execute DELETE request
- `head(url, **kwargs)`: Execute HEAD request
- `options(url, **kwargs)`: Execute OPTIONS request
- `close()`: Close the client and cleanup resources

### Request Builder

**Methods:**
- `set_query_param(key, value)`: Set single query parameter
- `set_query_params(params)`: Set multiple query parameters
- `set_header(key, value)`: Set single header
- `set_headers(headers)`: Set multiple headers
- `set_cookie(key, value)`: Set single cookie
- `set_cookies(cookies)`: Set multiple cookies
- `set_json(data)`: Set JSON body
- `set_form_data(data)`: Set form data
- `set_body(data)`: Set raw body
- `set_timeout(timeout)`: Set request timeout
- `set_follow_redirects(follow)`: Set redirect behavior
- `set_max_retries(retries)`: Set max retry attempts
- `set_auth(username, password)`: Set basic authentication
- `get(url)`: Execute GET request
- `post(url)`: Execute POST request
- `put(url)`: Execute PUT request
- `patch(url)`: Execute PATCH request
- `delete(url)`: Execute DELETE request
- `head(url)`: Execute HEAD request
- `options(url)`: Execute OPTIONS request

### RateLimitConfig

Configuration for parsing rate limit headers from different platforms.

**Parameters:**
- `name`: Configuration name for identification
- `reset_headers`: List of header names containing reset timestamp (Unix time)
- `remaining_headers`: List of header names containing remaining request count
- `limit_headers`: List of header names containing rate limit
- `retry_after_headers`: List of header names containing retry delay in seconds
- `custom_parser`: Optional function `(headers: dict) -> Optional[float]` for custom parsing
- `priority`: Priority level (higher = checked first, default: 0)

**Predefined Configs:**
- `CLOUDFLARE`: Cloudflare CDN (`cf-ratelimit-*`)
- `GITHUB`: GitHub API (`x-ratelimit-*`)
- `TWITTER`: Twitter API (`x-rate-limit-*`)
- `BINANCE`: Binance exchange (`x-mbx-*`, weight-based)
- `STANDARD_HTTP`: Standard HTTP headers (`x-ratelimit-*`, `retry-after`)

**Example:**
```python
from xttp import RateLimitConfig

config = RateLimitConfig(
    name="my-api",
    reset_headers=["x-custom-reset"],
    remaining_headers=["x-custom-remaining"],
    priority=10,
)
```

## Best Practices

1. **Always use async context manager** to ensure proper cleanup:
   ```python
   async with HTTPClient(...) as client:
       # Your code here
   ```

2. **Set appropriate rate limits** to avoid overwhelming APIs:
   ```python
   client = HTTPClient(rate_limit=100, rate_limit_window=60.0)
   ```

3. **Use default configs for common platforms**:
   ```python
   # No need to specify configs for common platforms
   async with HTTPClient(rate_limit=100) as client:
       # Automatically supports Cloudflare, GitHub, Binance, etc.
       ...
   ```

4. **Specify platform configs for better performance**:
   ```python
   from xttp import HTTPClient, GITHUB

   # If you know the platform, specify it
   async with HTTPClient(rate_limit=5000, rate_limit_configs=[GITHUB]) as client:
       ...
   ```

5. **Use custom configs for non-standard APIs**:
   ```python
   from xttp import RateLimitConfig

   config = RateLimitConfig(
       name="my-api",
       reset_headers=["x-custom-reset"],
       priority=10,
   )
   ```

6. **Use fluent API for complex requests**:
   ```python
   response = await client.request().set_query_param(...).set_header(...).get(...)
   ```

7. **Handle errors appropriately**:
   ```python
   try:
       response = await client.get(...)
       response.raise_for_status()
   except HTTPClientError as e:
       # Handle error
   ```

8. **Set base_url** to avoid repetition:
   ```python
   client = HTTPClient(base_url="https://api.example.com")
   response = await client.get("/users")  # Full URL: https://api.example.com/users
   ```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ackness/xttp.git
cd xttp

# Install dependencies (using uv)
uv sync --dev
```

### Code Quality

The project uses `ruff` for linting and formatting:

```bash
# Format code
uv run ruff format .

# Check code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Testing

The project has a comprehensive test suite with 88+ tests covering:
- HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- Request builder (fluent API)
- Retry mechanism with exponential backoff
- Rate limiting with multiple platform configurations
- Exception handling
- Concurrent requests

**Run tests:**

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_client.py

# Run tests in parallel (faster)
uv run pytest -n auto

# Run with coverage report
uv run pytest --cov=src --cov-report=html
uv run pytest --cov=src --cov-report=term-missing
```

**Test structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── test_client.py           # Basic HTTP client tests (21 tests)
├── test_request_builder.py  # Fluent API tests (24 tests)
├── test_retry.py            # Retry mechanism tests (12 tests)
├── test_rate_limiter.py     # Rate limiting tests (10 tests)
└── test_exceptions.py       # Exception handling tests (21 tests)
```

All tests use `pytest-httpx` for mocking HTTP requests, ensuring fast and reliable test execution without making actual network calls.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to:
1. Update tests as appropriate
2. Run `uv run ruff format .` before committing
3. Ensure all tests pass with `uv run pytest`

## License

MIT
