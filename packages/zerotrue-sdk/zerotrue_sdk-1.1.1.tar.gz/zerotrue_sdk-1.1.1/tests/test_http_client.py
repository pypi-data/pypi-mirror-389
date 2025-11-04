"""Tests for HTTP client."""

from zerotrue.http_client import HTTPClient


def test_http_client_initialization():
    """Test HTTP client initialization."""
    client = HTTPClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.base_url == "https://app.zerotrue.app"


def test_http_client_custom_options():
    """Test HTTP client with custom options."""
    client = HTTPClient(
        api_key="test_key",
        base_url="https://custom.url",
        timeout=60000,
        max_retries=5,
        retry_delay=2000,
        debug=True,
    )
    assert client.base_url == "https://custom.url"
    assert client.timeout == 60.0
    assert client.max_retries == 5
    assert client.retry_delay == 2.0
