"""ZeroTrue Python SDK - Official SDK for ZeroTrue AI Detection API."""

from zerotrue.async_client import AsyncZeroTrue
from zerotrue.client import ZeroTrue
from zerotrue.exceptions import APIError, AuthenticationError, RateLimitError, ValidationError

__version__ = "1.2.0"
__all__ = [
    "ZeroTrue",
    "AsyncZeroTrue",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
]
