"""Async ZeroTrue client."""

from zerotrue.http_client import AsyncHTTPClient
from zerotrue.resources.async_checks import AsyncChecks


class AsyncZeroTrue:
    """Async client for ZeroTrue API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.zerotrue.app",
        timeout: int = 30000,
        max_retries: int = 3,
        retry_delay: int = 1000,
        debug: bool = False,
    ):
        """
        Initialize async ZeroTrue client.

        Args:
            api_key: Your ZeroTrue API key
            base_url: API base URL (default: https://app.zerotrue.app)
            timeout: Request timeout in milliseconds (default: 30000)
            max_retries: Max retry attempts (default: 3)
            retry_delay: Delay between retries in milliseconds (default: 1000)
            debug: Enable debug logging (default: False)
        """
        if not api_key:
            raise ValueError("api_key is required")

        self._http_client = AsyncHTTPClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            debug=debug,
        )
        self.checks = AsyncChecks(self._http_client)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the async client and cleanup resources."""
        await self._http_client.close()
