"""Type definitions for ZeroTrue SDK."""

from typing import Any, Dict, List, Literal, Optional, TypedDict

CheckStatus = Literal["queued", "processing", "completed", "failed", "canceled", "expired"]


class InputDict(TypedDict):
    """Input dictionary for check creation."""

    type: Literal["text", "url"]
    value: str


class CheckResponse(TypedDict):
    """Response from check creation."""

    id: str
    status: CheckStatus
    created_at: str


class SuspectedModel(TypedDict):
    """Suspected AI model information."""

    model_name: str
    confidence_pct: float


class Segment(TypedDict, total=False):
    """Segment information for detailed analysis."""

    label: str
    confidence_pct: float
    start_char: Optional[int]
    end_char: Optional[int]
    start_s: Optional[float]
    end_s: Optional[float]


class CheckResult(CheckResponse, total=False):
    """Extended check result with analysis data."""

    ai_probability: Optional[float]
    human_probability: Optional[float]
    combined_probability: Optional[float]
    result_type: Optional[str]
    ml_model: Optional[str]
    ml_model_version: Optional[str]
    file_url: Optional[str]
    original_filename: Optional[str]
    size_bytes: Optional[int]
    size_mb: Optional[float]
    resolution: Optional[str]
    length: Optional[int]
    suspected_models: Optional[List[SuspectedModel]]
    segments: Optional[List[Segment]]
    metadata: Optional[Dict[str, Any]]


class CreateCheckParams(TypedDict, total=False):
    """Parameters for creating a check."""

    input: InputDict
    isPrivateScan: bool
    isDeepScan: bool
    idempotencyKey: Optional[str]
    metadata: Optional[Dict[str, Any]]


class WaitOptions(TypedDict, total=False):
    """Options for waiting for check completion."""

    pollInterval: int
    maxPollTime: int
    signal: Any  # For cancellation support (similar to AbortSignal)
