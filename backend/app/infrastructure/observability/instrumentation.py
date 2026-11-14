from contextlib import asynccontextmanager

from app.services.metrics_service import MetricsService


@asynccontextmanager
async def track_request(metrics: MetricsService):
    metrics.start()
    try:
        yield
    finally:
        metrics.finish()
