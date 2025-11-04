"""Custom exceptions for ZeroTrue SDK."""


class ZeroTrueError(Exception):
    """Base exception for all ZeroTrue SDK errors."""

    pass


class APIError(ZeroTrueError):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(APIError):
    """Exception raised for rate limit errors."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(ZeroTrueError):
    """Exception raised for validation errors."""

    pass
