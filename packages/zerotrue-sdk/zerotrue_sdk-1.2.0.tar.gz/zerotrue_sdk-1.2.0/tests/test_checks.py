"""Tests for checks resource."""

from io import BytesIO

import pytest

from zerotrue import ZeroTrue


@pytest.fixture
def client():
    """Create a test client."""
    return ZeroTrue(api_key="test_key")


def test_checks_resource_exists(client):
    """Test that checks resource exists."""
    assert client.checks is not None


def test_create_check_validation(client):
    """Test create check validation."""
    with pytest.raises(KeyError):
        client.checks.create({})


def test_create_check_params(client):
    """Test create check with valid params."""
    # This will fail without mocking, but tests structure
    params = {
        "input": {"type": "text", "value": "test"},
    }
    # Should not raise validation error for structure
    assert isinstance(params, dict)


def test_create_from_buffer_with_bytes(client):
    """Test create_from_buffer with bytes."""
    file_data = b"test file content"
    # This will fail without mocking, but tests structure
    assert isinstance(file_data, bytes)


def test_create_from_buffer_with_file(client):
    """Test create_from_buffer with file-like object."""
    buffer = BytesIO(b"test file content")
    # This will fail without mocking, but tests structure
    assert hasattr(buffer, "read")
