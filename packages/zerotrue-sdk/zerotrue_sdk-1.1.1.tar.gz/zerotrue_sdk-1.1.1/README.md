# ZeroTrue Python SDK

Official Python SDK for ZeroTrue AI Detection API - Detect AI-generated content in text, images, videos, and audio.

## Features

- **Sync & Async support** - Choose what fits your needs
- Full type hints support
- Automatic retry on failures with exponential backoff
- Rate limit handling with smart backoff
- Idempotency support for safe retries
- File upload support (bytes, file path, file-like objects)
- Auto-polling for check results
- Minimal dependencies (only httpx)

## Requirements

- Python 3.8 or higher
- Supports Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

## Installation

```bash
pip install zerotrue-sdk
```

Or with poetry:

```bash
poetry add zerotrue-sdk
```

## Quick Start

### Sync Usage

```python
from zerotrue import ZeroTrue
import os

client = ZeroTrue(
    api_key=os.getenv("ZEROTRUE_API_KEY"),
)

# Check text for AI generation
result = client.checks.create_and_wait({
    "input": {"type": "text", "value": "Check this text..."},
})

print(f"AI Probability: {result.get('ai_probability', 0)}%")
print(f"Result: {result.get('result_type', 'unknown')}")
```

### Async Usage

```python
from zerotrue import AsyncZeroTrue
import asyncio
import os

async def main():
    async with AsyncZeroTrue(api_key=os.getenv("ZEROTRUE_API_KEY")) as client:
        # Check text for AI generation
        result = await client.checks.create_and_wait({
            "input": {"type": "text", "value": "Check this text..."},
        })

        print(f"AI Probability: {result.get('ai_probability', 0)}%")

asyncio.run(main())
```

### Parallel Async Requests (Fast! 🚀)

```python
async def check_multiple():
    async with AsyncZeroTrue(api_key=os.getenv("ZEROTRUE_API_KEY")) as client:
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]

        # All checks run in parallel!
        tasks = [
            client.checks.create_and_wait({"input": {"type": "text", "value": text}})
            for text in texts
        ]

        results = await asyncio.gather(*tasks)
        return results
```

## Usage

### Initialize Client

```python
client = ZeroTrue(
    api_key="zt_your_api_key_here",
    base_url="https://app.zerotrue.app",  # optional
    timeout=30000,  # 30 seconds (optional)
    max_retries=3,  # retry failed requests (optional)
    retry_delay=1000,  # 1 second between retries (optional)
    debug=False,  # enable debug logging (optional)
)
```

### Check Text

```python
check = client.checks.create({
    "input": {
        "type": "text",
        "value": "Your text to analyze...",
    },
    "isPrivateScan": True,  # default
    "isDeepScan": False,  # default
})

# Get result
result = client.checks.retrieve(check["id"])

# Or wait for completion
result = client.checks.wait(check["id"])
```

### Check URL

```python
check = client.checks.create({
    "input": {
        "type": "url",
        "value": "https://example.com/image.png",
    },
})
```

### Check File

#### From file path

```python
check = client.checks.create_from_file("./image.png", {
    "isPrivateScan": True,
    "isDeepScan": False,
})
```

#### From buffer

```python
with open("./image.png", "rb") as f:
    check = client.checks.create_from_buffer(f, "image.png")
```

#### From bytes

```python
with open("./image.png", "rb") as f:
    file_bytes = f.read()

check = client.checks.create_from_buffer(file_bytes, "image.png")
```

### Wait for Result

```python
# Simple wait
result = client.checks.wait(check_id)

# With custom options
result = client.checks.wait(check_id, {
    "pollInterval": 2000,  # 2 seconds (default)
    "maxPollTime": 300000,  # 5 minutes (default)
})

# With cancellation support
import threading
cancel_signal = threading.Event()

try:
    result = client.checks.wait(check_id, {
        "pollInterval": 2000,
        "maxPollTime": 300000,
        "signal": cancel_signal,  # For cancellation
    })
except InterruptedError:
    print("Wait was cancelled")
```

### Create and Wait (One-liner)

```python
result = client.checks.create_and_wait({
    "input": {"type": "text", "value": "Check this..."},
})

print(f"AI Probability: {result.get('ai_probability', 0)}")
```

### Idempotency

```python
check = client.checks.create({
    "input": {"type": "text", "value": "Test"},
    "idempotencyKey": "unique-request-id-123",  # Reusing same key returns cached response
})
```

## Error Handling

```python
from zerotrue import ZeroTrue
from zerotrue.exceptions import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    APIError,
)

try:
    check = client.checks.create({
        "input": {"type": "text", "value": "Test"},
    })
except ValidationError as e:
    print(f"Validation failed: {e}")
except AuthenticationError as e:
    print(f"Invalid API key: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
except APIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
except Exception as e:
    print(f"Unknown error: {e}")
```

## API Reference

### Client Methods

#### `ZeroTrue(options)`

Creates a new ZeroTrue client.

**Options:**

- `api_key` (str, required) - Your ZeroTrue API key
- `base_url` (str, optional) - API base URL (default: `https://app.zerotrue.app`)
- `timeout` (int, optional) - Request timeout in ms (default: `30000`)
- `max_retries` (int, optional) - Max retry attempts (default: `3`)
- `retry_delay` (int, optional) - Delay between retries in ms (default: `1000`)
- `debug` (bool, optional) - Enable debug logging (default: `False`)

### Checks Resource

#### `client.checks.create(params)`

Creates a new check.

**Parameters:**

- `input` (dict, required) - Input to check:
  - `type` (str) - `"text"` or `"url"`
  - `value` (str) - Text content or URL
- `isPrivateScan` (bool, optional) - Private scan (default: `True`)
- `isDeepScan` (bool, optional) - Deep scan (default: `False`)
- `idempotencyKey` (str, optional) - Idempotency key
- `metadata` (dict, optional) - Additional metadata

**Returns:** `CheckResponse`

#### `client.checks.create_from_file(file_path, options?)`

Creates a check from a file path.

**Returns:** `CheckResponse`

#### `client.checks.create_from_buffer(buffer, filename, options?)`

Creates a check from a buffer (bytes, BytesIO, or file-like object).

**Returns:** `CheckResponse`

#### `client.checks.retrieve(check_id)`

Retrieves a check by ID.

**Returns:** `CheckResult`

#### `client.checks.wait(check_id, options?)`

Waits for a check to complete.

**Options:**

- `pollInterval` (int) - Polling interval in ms (default: `2000`)
- `maxPollTime` (int) - Max wait time in ms (default: `300000`)
- `signal` (threading.Event) - For cancellation (optional)

**Returns:** `CheckResult`

#### `client.checks.create_and_wait(params, options?)`

Creates a check and waits for completion.

**Returns:** `CheckResult`

## Types

### CheckResponse

```python
{
    "id": str,
    "status": "queued" | "processing" | "completed" | "failed" | "canceled" | "expired",
    "created_at": str,
}
```

### CheckResult

Extends `CheckResponse` with additional fields:

```python
{
    # ... CheckResponse fields
    "ai_probability": float | None,
    "human_probability": float | None,
    "combined_probability": float | None,
    "result_type": str | None,
    "ml_model": str | None,
    "ml_model_version": str | None,
    "file_url": str | None,
    "original_filename": str | None,
    "size_bytes": int | None,
    "size_mb": float | None,
    "resolution": str | None,
    "length": int | None,
    "suspected_models": List[Dict[str, Any]] | None,
    "segments": List[Dict[str, Any]] | None,
    # ... and more
}
```

## Rate Limits

- **60 requests per minute**
- **10,000 requests per day**

The SDK automatically handles rate limits with retry logic.

## Supported File Formats

- **Images:** jpg, jpeg, png, gif, bmp, tiff, webp
- **Videos:** mp4, mov, avi, mkv, webm
- **Audio:** mp3, wav, ogg, flac
- **Code:** py, js, ts, html, css, java, cpp, go, json, txt

## Environment Variables

```bash
# .env
ZEROTRUE_API_KEY=zt_your_api_key_here
```

## Examples

See the `examples/` directory for more examples:

**Sync examples:**
- `basic.py` - Basic usage
- `file_check.py` - File upload examples
- `error_handling.py` - Error handling
- `advanced.py` - Advanced usage patterns
- `cancellation.py` - Cancelling wait operations

**Async examples:**
- `async_basic.py` - Basic async usage
- `async_parallel.py` - Parallel requests (fast!)
- `async_vs_sync.py` - Performance comparison

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy zerotrue
```

## License

MIT

## Support

- Documentation: https://app.zerotrue.app/docs
- Issues: [GitHub Issues](https://github.com/ZeroTrueLCC/sdk-python/issues)
- Email: support@zerotrue.ai

