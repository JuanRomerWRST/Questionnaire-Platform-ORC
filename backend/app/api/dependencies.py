import asyncio

from fastapi import Request

from app.core.config import Settings, get_settings
from app.infrastructure.llm.openai_provider import build_llm_provider
from app.infrastructure.observability.request_context import current_request_id
from app.infrastructure.ocr.tesseract_engine import TesseractEngine
from app.services.document_service import ProcessDeps
from app.services.metrics_service import MetricsService


def ensure_state(app) -> None:
    if getattr(app.state, "ready", False):
        return
    settings = get_settings()
    app.state.settings = settings
    app.state.metrics = MetricsService()
    app.state.request_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
    app.state.ocr_semaphore = asyncio.Semaphore(settings.max_concurrent_ocr)
    app.state.llm_semaphore = asyncio.Semaphore(settings.openai_max_concurrent_requests)
    app.state.llm_provider = build_llm_provider(settings)
    app.state.ocr_engine = TesseractEngine(settings)
    app.state.ready = True


def get_process_deps(request: Request) -> ProcessDeps:
    ensure_state(request.app)
    return ProcessDeps(
        settings=request.app.state.settings,
        request_id=current_request_id(request),
        metrics=request.app.state.metrics,
        request_semaphore=request.app.state.request_semaphore,
        ocr_semaphore=request.app.state.ocr_semaphore,
        llm_semaphore=request.app.state.llm_semaphore,
        llm_provider=request.app.state.llm_provider,
        ocr_engine=request.app.state.ocr_engine,
    )


def get_app_settings(request: Request) -> Settings:
    ensure_state(request.app)
    return request.app.state.settings
