"""HTTP client for ZeroTrue API requests."""

import logging
from typing import Any, Dict, Optional

import httpx

from zerotrue.exceptions import APIError, AuthenticationError, RateLimitError, ValidationError

logger = logging.getLogger(__name__)


class HTTPClient:
    """Sync HTTP client with retry logic and error handling."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.zerotrue.app",
        timeout: int = 30000,
        max_retries: int = 3,
        retry_delay: int = 1000,
        debug: bool = False,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout / 1000  # Convert to seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay / 1000  # Convert to seconds
        self.debug = debug

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

        # Setup httpx client with retry
        # Не устанавливаем Content-Type по умолчанию, он будет добавляться автоматически при необходимости
        transport = httpx.HTTPTransport(retries=max_retries)
        self.client = httpx.Client(
            transport=transport,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
        )

    def __del__(self):
        """Close client on cleanup."""
        if hasattr(self, "client"):
            self.client.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if self.debug:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")

        if response.status_code in (200, 201):
            return response.json()

        if response.status_code == 400:
            error_data = response.json() if response.text else {}
            raise ValidationError(error_data.get("message", "Validation error") or "Validation error")

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", status_code=401)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=retry_after,
                status_code=429,
                response=response.json() if response.text else {},
            )

        error_data = response.json() if response.text else {}
        raise APIError(
            error_data.get("message", f"API error: {response.status_code}") or f"API error: {response.status_code}",
            status_code=response.status_code,
            response=error_data,
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{path}"

        request_headers = dict(self.client.headers)
        if headers:
            request_headers.update(headers)

        # Устанавливаем Content-Type только для JSON запросов
        # Для form-data (data) и file uploads httpx установит Content-Type автоматически
        if json and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"

        if self.debug:
            logger.debug(f"{method} {url}")
            logger.debug(f"Headers: {request_headers}")
            if params:
                logger.debug(f"Params: {params}")
            if json:
                logger.debug(f"JSON: {json}")
            if data:
                logger.debug(f"Data: {data}")

        try:
            # httpx автоматически использует application/x-www-form-urlencoded для data без files
            response = self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=request_headers,
            )
            return self._handle_response(response)
        except (AuthenticationError, ValidationError, RateLimitError):
            raise
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}") from e

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self.request("POST", path, json=json, data=data, files=files, headers=headers)


class AsyncHTTPClient:
    """Async HTTP client with retry logic and error handling."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.zerotrue.app",
        timeout: int = 30000,
        max_retries: int = 3,
        retry_delay: int = 1000,
        debug: bool = False,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout / 1000  # Convert to seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay / 1000  # Convert to seconds
        self.debug = debug

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

        # Setup httpx async client with retry
        # Не устанавливаем Content-Type по умолчанию, он будет добавляться автоматически при необходимости
        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self.client = httpx.AsyncClient(
            transport=transport,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def close(self):
        """Close async client."""
        await self.client.aclose()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if self.debug:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")

        if response.status_code in (200, 201):
            return response.json()

        if response.status_code == 400:
            error_data = response.json() if response.text else {}
            raise ValidationError(error_data.get("message", "Validation error") or "Validation error")

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", status_code=401)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=retry_after,
                status_code=429,
                response=response.json() if response.text else {},
            )

        error_data = response.json() if response.text else {}
        raise APIError(
            error_data.get("message", f"API error: {response.status_code}") or f"API error: {response.status_code}",
            status_code=response.status_code,
            response=error_data,
        )

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async HTTP request with retry logic."""
        url = f"{self.base_url}{path}"

        request_headers = dict(self.client.headers)
        if headers:
            request_headers.update(headers)

        # Устанавливаем Content-Type только для JSON запросов
        # Для form-data (data) и file uploads httpx установит Content-Type автоматически
        if json and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"

        if self.debug:
            logger.debug(f"{method} {url}")
            logger.debug(f"Headers: {request_headers}")
            if params:
                logger.debug(f"Params: {params}")
            if json:
                logger.debug(f"JSON: {json}")
            if data:
                logger.debug(f"Data: {data}")

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=request_headers,
            )
            return self._handle_response(response)
        except (AuthenticationError, ValidationError, RateLimitError):
            raise
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}") from e

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make async GET request."""
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async POST request."""
        return await self.request("POST", path, json=json, data=data, files=files, headers=headers)
