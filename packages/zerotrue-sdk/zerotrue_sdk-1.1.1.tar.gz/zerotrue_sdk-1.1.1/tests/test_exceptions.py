"""Tests for exceptions."""

from zerotrue.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ZeroTrueError,
)


def test_api_error():
    """Test APIError exception."""
    error = APIError("Test error", status_code=500)
    assert str(error) == "Test error"
    assert error.status_code == 500


def test_authentication_error():
    """Test AuthenticationError exception."""
    error = AuthenticationError("Invalid API key", status_code=401)
    assert str(error) == "Invalid API key"
    assert error.status_code == 401


def test_rate_limit_error():
    """Test RateLimitError exception."""
    error = RateLimitError("Rate limit exceeded", retry_after=60)
    assert str(error) == "Rate limit exceeded"
    assert error.retry_after == 60


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Validation failed")
    assert str(error) == "Validation failed"


def test_inheritance():
    """Test exception inheritance."""
    assert issubclass(APIError, ZeroTrueError)
    assert issubclass(AuthenticationError, APIError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(ValidationError, ZeroTrueError)
