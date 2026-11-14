import math
import threading
import time
from collections import deque

from app.schemas.metrics import AggregatedMetrics, ProcessingMetrics


class MetricsService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._samples: deque[ProcessingMetrics] = deque(maxlen=1000)
        self._in_flight = 0
        self._max_concurrency = 0
        self._started = time.perf_counter()
        self._llm_errors = 0

    def start(self) -> None:
        with self._lock:
            self._in_flight += 1
            self._max_concurrency = max(self._max_concurrency, self._in_flight)

    def finish(self) -> None:
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)

    def record(self, metrics: ProcessingMetrics, *, llm_error: bool = False) -> None:
        with self._lock:
            self._samples.append(metrics)
            if llm_error:
                self._llm_errors += 1

    def snapshot(self) -> AggregatedMetrics:
        with self._lock:
            samples = list(self._samples)
            in_flight = self._in_flight
            max_concurrency = self._max_concurrency
            elapsed = max(time.perf_counter() - self._started, 0.001)
            llm_errors = self._llm_errors
        total = len(samples)
        latencies = [sample.total_processing_ms for sample in samples]
        success = sum(1 for sample in samples if sample.status == "success")
        partial = sum(1 for sample in samples if sample.status == "partial")
        failed = sum(1 for sample in samples if sample.status == "failed")
        llm_used = sum(1 for sample in samples if sample.llm_used)
        stages = (
            "validation_ms",
            "parsing_ms",
            "ocr_ms",
            "deterministic_extraction_ms",
            "llm_ms",
            "validation_output_ms",
        )
        averages = {
            stage: round(sum(getattr(sample, stage) for sample in samples) / total, 2) if total else 0
            for stage in stages
        }
        return AggregatedMetrics(
            requests_total=total,
            requests_success=success,
            requests_failed=failed,
            requests_partial=partial,
            in_flight=in_flight,
            max_concurrency=max_concurrency,
            latency_avg_ms=round(sum(latencies) / total, 2) if total else 0,
            latency_p50_ms=_percentile(latencies, 50),
            latency_p95_ms=_percentile(latencies, 95),
            latency_p99_ms=_percentile(latencies, 99),
            throughput_rps=round(total / elapsed, 4),
            avg_stage_ms=averages,
            llm_usage_ratio=round(llm_used / total, 4) if total else 0,
            llm_error_rate=round(llm_errors / llm_used, 4) if llm_used else 0,
            tokens_input_total=sum(sample.input_tokens or 0 for sample in samples),
            tokens_output_total=sum(sample.output_tokens or 0 for sample in samples),
        )


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    if percentile >= 99 and len(values) < 100:
        return None
    if percentile >= 95 and len(values) < 20:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (percentile / 100)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return round(ordered[low], 2)
    weight = rank - low
    return round(ordered[low] * (1 - weight) + ordered[high] * weight, 2)
