from fastapi import APIRouter, Request

from app.api.dependencies import ensure_state
from app.core.exceptions import AppError
from app.schemas.metrics import AggregatedMetrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=AggregatedMetrics)
def metrics(request: Request) -> AggregatedMetrics:
    ensure_state(request.app)
    settings = request.app.state.settings
    if settings.metrics_token:
        header = request.headers.get("authorization", "")
        if header != f"Bearer {settings.metrics_token}":
            raise AppError(401, "UNAUTHORIZED", "No tiene acceso a las métricas.")
    return request.app.state.metrics.snapshot()
