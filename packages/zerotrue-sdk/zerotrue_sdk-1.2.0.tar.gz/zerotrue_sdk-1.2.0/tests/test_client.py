"""Tests for ZeroTrue client."""

import pytest

from zerotrue import ZeroTrue


def test_client_initialization():
    """Test client initialization."""
    client = ZeroTrue(api_key="test_key")
    assert client.checks is not None


def test_client_initialization_without_api_key():
    """Test client initialization fails without API key."""
    with pytest.raises(ValueError):
        ZeroTrue(api_key="")


def test_client_initialization_with_options():
    """Test client initialization with custom options."""
    client = ZeroTrue(
        api_key="test_key",
        base_url="https://custom.url",
        timeout=60000,
        max_retries=5,
        retry_delay=2000,
        debug=True,
    )
    assert client.checks is not None
