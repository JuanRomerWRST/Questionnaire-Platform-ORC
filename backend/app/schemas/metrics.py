from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProcessingMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    file_type: str
    file_size_bytes: int
    pages_or_sheets: int | None = None
    validation_ms: float = 0
    parsing_ms: float = 0
    ocr_ms: float = 0
    deterministic_extraction_ms: float = 0
    llm_ms: float = 0
    validation_output_ms: float = 0
    total_processing_ms: float = 0
    llm_used: bool = False
    llm_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    items_detected: int = 0
    warnings_count: int = 0
    status: Literal["success", "partial", "failed"]
    extraction_method: Literal["text", "ocr", "llm_text", "llm_vision"] = "text"
    confidence_score: float = 0


class AggregatedMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: str = "process-local, in-memory, resets on restart"
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    requests_partial: int = 0
    in_flight: int = 0
    max_concurrency: int = 0
    latency_avg_ms: float = 0
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    latency_p99_ms: float | None = None
    throughput_rps: float = 0
    avg_stage_ms: dict[str, float] = Field(default_factory=dict)
    llm_usage_ratio: float = 0
    llm_error_rate: float = 0
    tokens_input_total: int = 0
    tokens_output_total: int = 0
