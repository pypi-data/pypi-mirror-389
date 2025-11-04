"""Checks resource for ZeroTrue SDK."""

import os
import time
from io import BytesIO
from typing import Any, BinaryIO, Dict, Optional, Union

from zerotrue.http_client import HTTPClient
from zerotrue.types import CheckResponse, CheckResult, CreateCheckParams, WaitOptions


class Checks:
    """Resource for managing checks."""

    def __init__(self, client: HTTPClient):
        self._client = client

    def create(self, params: CreateCheckParams) -> CheckResponse:
        """
        Create a new check.

        Args:
            params: Parameters for check creation

        Returns:
            CheckResponse with check ID and status
        """
        payload: Dict[str, Any] = {
            "input": params["input"],
        }

        if "isPrivateScan" in params:
            payload["is_private_scan"] = params["isPrivateScan"]
        else:
            payload["is_private_scan"] = True

        if "isDeepScan" in params:
            payload["is_deep_scan"] = params["isDeepScan"]
        else:
            payload["is_deep_scan"] = False

        if "idempotencyKey" in params and params["idempotencyKey"]:
            payload["idempotency_key"] = params["idempotencyKey"]

        if "metadata" in params and params["metadata"]:
            payload["metadata"] = params["metadata"]

        headers = {}
        if "idempotencyKey" in params and params["idempotencyKey"]:
            headers["Idempotency-Key"] = params["idempotencyKey"]

        response = self._client.post("/api/v1/checks", json=payload, headers=headers)
        return response  # type: ignore

    def create_from_file(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> CheckResponse:
        """
        Create a check from a file path.

        Args:
            file_path: Path to the file
            options: Optional parameters (isPrivateScan, isDeepScan, etc.)

        Returns:
            CheckResponse with check ID and status
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        options = options or {}
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            return self.create_from_buffer(f, filename, options)

    def create_from_buffer(
        self,
        buffer: Union[BinaryIO, bytes, BytesIO],
        filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> CheckResponse:
        """
        Create a check from a buffer.

        Args:
            buffer: File-like object (opened in binary mode), bytes, or BytesIO
            filename: Name of the file
            options: Optional parameters (isPrivateScan, isDeepScan, etc.)

        Returns:
            CheckResponse with check ID and status
        """
        options = options or {}

        payload: Dict[str, Any] = {}
        if "isPrivateScan" in options:
            payload["is_private_scan"] = options["isPrivateScan"]
        else:
            payload["is_private_scan"] = True

        if "isDeepScan" in options:
            payload["is_deep_scan"] = options["isDeepScan"]
        else:
            payload["is_deep_scan"] = False

        if "idempotencyKey" in options and options["idempotencyKey"]:
            payload["idempotency_key"] = options["idempotencyKey"]

        if "metadata" in options and options["metadata"]:
            payload["metadata"] = options["metadata"]

        # Handle different buffer types
        if isinstance(buffer, bytes):
            file_data = buffer
        elif hasattr(buffer, "read"):
            # Save current position if seek is supported
            if hasattr(buffer, "seek"):
                current_pos = buffer.tell() if hasattr(buffer, "tell") else 0
                buffer.seek(0)
            file_data = buffer.read()
            # Restore position if possible
            if hasattr(buffer, "seek"):
                buffer.seek(current_pos)
        else:
            raise ValueError("buffer must be bytes, BytesIO, or file-like object")

        files = {
            "file": (filename, file_data, self._get_content_type(filename)),
        }

        # Prepare form data
        form_data = {}
        for key, value in payload.items():
            if value is not None:
                if isinstance(value, bool):
                    form_data[key] = str(value).lower()
                elif isinstance(value, dict):
                    import json

                    form_data[key] = json.dumps(value)
                else:
                    form_data[key] = str(value)

        headers = {}
        if "idempotencyKey" in options and options["idempotencyKey"]:
            headers["Idempotency-Key"] = options["idempotencyKey"]

        response = self._client.post(
            "/api/v1/checks/upload",
            files=files,
            data=form_data if form_data else None,
            headers=headers,
        )
        return response  # type: ignore

    def retrieve(self, check_id: str) -> CheckResult:
        """
        Retrieve a check by ID.

        Args:
            check_id: Check ID

        Returns:
            CheckResult with analysis data
        """
        response = self._client.get(f"/api/v1/checks/{check_id}")
        return response  # type: ignore

    def wait(
        self,
        check_id: str,
        options: Optional[WaitOptions] = None,
    ) -> CheckResult:
        """
        Wait for a check to complete.

        Args:
            check_id: Check ID
            options: Wait options (pollInterval, maxPollTime, signal)

        Returns:
            CheckResult with analysis data

        Raises:
            TimeoutError: If check doesn't complete within maxPollTime
            InterruptedError: If operation was cancelled via signal
        """
        options = options or {}
        poll_interval = options.get("pollInterval", 2000) / 1000  # Convert to seconds
        max_poll_time = options.get("maxPollTime", 300000) / 1000  # Convert to seconds
        signal = options.get("signal")

        start_time = time.time()

        while True:
            # Check if operation was cancelled (similar to AbortSignal)
            if signal and hasattr(signal, "is_set") and signal.is_set():
                raise InterruptedError(f"Wait operation for check {check_id} was cancelled")

            result = self.retrieve(check_id)

            if result["status"] == "completed":
                return result

            if result["status"] in ("failed", "canceled", "expired"):
                raise RuntimeError(f"Check {check_id} failed with status: {result['status']}")

            if time.time() - start_time > max_poll_time:
                raise TimeoutError(f"Check {check_id} did not complete within {max_poll_time} seconds")

            time.sleep(poll_interval)

    def create_and_wait(
        self,
        params: CreateCheckParams,
        options: Optional[WaitOptions] = None,
    ) -> CheckResult:
        """
        Create a check and wait for completion.

        Args:
            params: Parameters for check creation
            options: Wait options (pollInterval, maxPollTime)

        Returns:
            CheckResult with analysis data
        """
        check = self.create(params)
        return self.wait(check["id"], options)

    @staticmethod
    def _get_content_type(filename: str) -> str:
        """Get content type based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".html": "text/html",
            ".css": "text/css",
            ".java": "text/x-java-source",
            ".cpp": "text/x-c++src",
            ".go": "text/x-go",
            ".json": "application/json",
            ".txt": "text/plain",
        }
        return content_types.get(ext, "application/octet-stream")
