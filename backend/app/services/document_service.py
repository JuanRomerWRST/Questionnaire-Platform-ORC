import asyncio
import io
import logging
from dataclasses import dataclass

from fastapi import UploadFile
from PIL import Image

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.limits import LLM_MAX_CALLS_PER_DOCUMENT, MIN_OCR_TEXT_CHARS
from app.domain.enums.document_type import DocumentType
from app.domain.interfaces.llm_provider import LLMRequest
from app.domain.interfaces.parser import ExtractedDocument
from app.infrastructure.llm.base import LLMAuthError, LLMError, LLMQuotaError
from app.infrastructure.llm.response_parser import parse_llm_payload
from app.infrastructure.observability.instrumentation import track_request
from app.infrastructure.observability.timers import StageTimer
from app.infrastructure.parsers.base import split_text_lines
from app.infrastructure.parsers.registry import get_parser
from app.schemas.document import ExtractOptions
from app.schemas.metrics import ProcessingMetrics
from app.schemas.questionnaire import Questionnaire
from app.schemas.responses import ExtractionResponse, WarningItem
from app.services.extraction_service import DeterministicResult, run_deterministic
from app.services.metrics_service import MetricsService
from app.utils.file_utils import read_upload_limited, safe_extension
from app.utils.mime_utils import sniff_document_type

logger = logging.getLogger(__name__)


@dataclass
class ProcessDeps:
    settings: Settings
    request_id: str
    metrics: MetricsService
    request_semaphore: asyncio.Semaphore
    ocr_semaphore: asyncio.Semaphore
    llm_semaphore: asyncio.Semaphore
    llm_provider: object
    ocr_engine: object


async def process_document(upload: UploadFile, options: ExtractOptions, deps: ProcessDeps) -> ExtractionResponse:
    if deps.request_semaphore.locked():
        raise AppError(
            429,
            "TOO_MANY_REQUESTS",
            "Hay demasiadas solicitudes en curso. Intente de nuevo en unos segundos.",
            {"Retry-After": "5"},
        )
    await deps.request_semaphore.acquire()
    timer = StageTimer()
    try:
        async with track_request(deps.metrics):
            try:
                return await asyncio.wait_for(
                    _process(upload, options, deps, timer),
                    timeout=deps.settings.request_timeout_seconds,
                )
            except TimeoutError as exc:
                _record_failure(deps, timer, "unknown")
                raise AppError(
                    504,
                    "PROCESSING_TIMEOUT",
                    "El procesamiento superó el tiempo límite.",
                ) from exc
    finally:
        deps.request_semaphore.release()


async def _process(
    upload: UploadFile,
    options: ExtractOptions,
    deps: ProcessDeps,
    timer: StageTimer,
) -> ExtractionResponse:
    with timer.stage("validation"):
        data = await read_upload_limited(upload, deps.settings.max_upload_bytes)
        extension = safe_extension(upload.filename)
        document_type = sniff_document_type(data, extension, deps.settings)
    with timer.stage("parsing"):
        extracted = await asyncio.to_thread(
            get_parser(document_type).parse,
            data,
            settings=deps.settings,
            force_ocr=options.force_ocr,
        )
    visual = {DocumentType.PDF, DocumentType.PNG, DocumentType.JPEG, DocumentType.WEBP}
    if options.force_ocr and document_type not in visual:
        extracted.warnings.append(("FORCE_OCR_NOT_APPLICABLE", "force_ocr solo aplica a PDF e imágenes."))
    ocr_ms, ocr_used, ocr_confidence = await _run_ocr(extracted, options, deps, timer, document_type)
    with timer.stage("deterministic"):
        deterministic = await asyncio.to_thread(
            run_deterministic,
            extracted,
            threshold=deps.settings.confidence_threshold,
            ocr_used=ocr_used,
            ocr_confidence=ocr_confidence,
        )
    questionnaire = deterministic.questionnaire
    warnings = list(deterministic.warnings)
    llm_ms = 0.0
    llm_used = False
    llm_model = None
    input_tokens = None
    output_tokens = None
    llm_error = False
    method = "ocr" if ocr_used and not _has_native_text(document_type, extracted) else "text"
    if ocr_used and document_type != DocumentType.PDF:
        method = "ocr"
    elif ocr_used and not extracted.lines:
        method = "ocr"
    want_llm = deps.settings.llm_configured if options.use_llm is None else options.use_llm
    if deps.settings.use_mock_llm and options.use_llm is not False:
        want_llm = True
    needs_llm = deterministic.confidence.needs_llm or (ocr_used and len(deterministic.text) < MIN_OCR_TEXT_CHARS)
    if needs_llm and want_llm and (deps.settings.llm_configured or deps.settings.use_mock_llm):
        llm_outcome = await _call_llm(extracted, deterministic, document_type, deps, timer)
        llm_ms = llm_outcome.llm_ms
        llm_used = llm_outcome.used
        llm_model = llm_outcome.model
        input_tokens = llm_outcome.input_tokens
        output_tokens = llm_outcome.output_tokens
        llm_error = llm_outcome.error
        warnings.extend(llm_outcome.warnings)
        if llm_outcome.questionnaire is not None:
            questionnaire = llm_outcome.questionnaire
            method = "llm_vision" if extracted.pending_ocr_images else "llm_text"
        elif llm_outcome.fatal is not None and questionnaire is None:
            _record_failure(deps, timer, document_type.value, llm_error=llm_error)
            raise llm_outcome.fatal
    elif needs_llm and not (deps.settings.llm_configured or deps.settings.use_mock_llm):
        warnings.append(
            ("LLM_NOT_CONFIGURED", "El modelo no está configurado; se conserva el resultado determinístico.")
        )
    elif needs_llm and options.use_llm is False:
        warnings.append(("LLM_DISABLED_BY_REQUEST", "El fallback al modelo fue desactivado para esta solicitud."))
    if questionnaire is None or not questionnaire.items:
        code = "NO_TEXT_EXTRACTED" if not deterministic.text else "NO_QUESTIONS_DETECTED"
        message = (
            "No se extrajo texto suficiente del documento."
            if code == "NO_TEXT_EXTRACTED"
            else "No se detectaron preguntas en el documento."
        )
        _record_failure(deps, timer, document_type.value, llm_error=llm_error)
        raise AppError(422, code, message)
    rescued = method.startswith("llm")
    partial = _is_partial(deterministic, warnings, rescued, llm_error)
    status = "partial" if partial else "success"
    with timer.stage("validation_output"):
        metrics = _metrics(
            deps,
            timer,
            document_type.value,
            len(data),
            extracted.pages_or_sheets,
            ocr_ms,
            llm_ms,
            llm_used,
            llm_model,
            input_tokens,
            output_tokens,
            questionnaire,
            warnings,
            status,
            method,
            deterministic.confidence.score,
        )
    deps.metrics.record(metrics, llm_error=llm_error)
    return ExtractionResponse(
        request_id=deps.request_id,
        status=status,
        questionnaire=questionnaire,
        metrics=metrics,
        warnings=[WarningItem(code=code, message=message) for code, message in warnings],
    )


@dataclass
class _LlmOutcome:
    questionnaire: Questionnaire | None = None
    warnings: list[tuple[str, str]] | None = None
    llm_ms: float = 0
    used: bool = False
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: bool = False
    fatal: AppError | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


async def _call_llm(extracted, deterministic: DeterministicResult, document_type, deps: ProcessDeps, timer: StageTimer):
    outcome = _LlmOutcome()
    draft = deterministic.questionnaire.model_dump() if deterministic.questionnaire else None
    request = LLMRequest(
        text=deterministic.text,
        images=extracted.pending_ocr_images,
        file_type=document_type.value,
        draft_payload=draft,
    )
    try:
        async with deps.llm_semaphore:
            with timer.stage("llm"):
                for _ in range(LLM_MAX_CALLS_PER_DOCUMENT):
                    result = await deps.llm_provider.extract(request)
        outcome.used = True
        outcome.model = result.model
        outcome.input_tokens = result.input_tokens
        outcome.output_tokens = result.output_tokens
        questionnaire, warnings = parse_llm_payload(result.payload)
        outcome.warnings = warnings
        outcome.questionnaire = questionnaire
        if questionnaire is None:
            outcome.error = True
            outcome.warnings.append(("LLM_FAILED", "No se pudo usar la respuesta del modelo."))
    except LLMQuotaError:
        outcome.error = True
        outcome.used = True
        outcome.warnings = [("LLM_QUOTA_EXCEEDED", "OpenAI no tiene saldo. Se conserva el resultado determinístico.")]
        if deterministic.questionnaire is None:
            outcome.fatal = AppError(
                503,
                "LLM_UNAVAILABLE",
                "El proveedor LLM no tiene saldo y no hay un resultado parcial.",
            )
    except LLMAuthError:
        outcome.error = True
        outcome.used = True
        outcome.warnings = [("LLM_FAILED", "OpenAI rechazó la autenticación.")]
        if deterministic.questionnaire is None:
            outcome.fatal = AppError(503, "LLM_UNAVAILABLE", "El proveedor LLM rechazó la autenticación.")
    except LLMError as exc:
        outcome.error = True
        outcome.used = True
        outcome.warnings = [("LLM_FAILED", str(exc))]
        if deterministic.questionnaire is None:
            outcome.fatal = AppError(503, "LLM_UNAVAILABLE", "El proveedor LLM no está disponible.")
    outcome.llm_ms = timer.durations.get("llm", 0)
    return outcome


async def _run_ocr(
    extracted: ExtractedDocument,
    options: ExtractOptions,
    deps: ProcessDeps,
    timer: StageTimer,
    document_type,
):
    if not extracted.pending_ocr_images:
        return 0.0, False, None
    engine = deps.ocr_engine
    if not engine.available():
        extracted.warnings.append(("OCR_UNAVAILABLE", "Tesseract no está disponible en este entorno."))
        return 0.0, False, None
    confidences: list[float] = []
    texts: list[str] = []
    async with deps.ocr_semaphore:
        with timer.stage("ocr"):
            for payload in extracted.pending_ocr_images:
                result = await asyncio.to_thread(_recognize, engine, payload, deps.settings.ocr_languages)
                texts.append(result.text)
                confidences.append(result.mean_confidence)
    ocr_lines = []
    for index, text in enumerate(texts, start=1):
        ocr_lines.extend(split_text_lines(text, index))
    native = sum(len(line.text) for line in extracted.lines)
    if options.force_ocr or native < 30 or document_type != DocumentType.PDF:
        extracted.lines = ocr_lines
    else:
        extracted.lines.extend(ocr_lines)
    mean = sum(confidences) / len(confidences) if confidences else None
    return timer.durations.get("ocr", 0), True, mean


def _recognize(engine, payload: bytes, languages: str):
    with Image.open(io.BytesIO(payload)) as image:
        return engine.recognize(image, languages)


def _has_native_text(document_type: DocumentType, extracted: ExtractedDocument) -> bool:
    return document_type == DocumentType.PDF and any(extracted.lines)


def _is_partial(deterministic: DeterministicResult, warnings, rescued: bool, llm_error: bool) -> bool:
    codes = {code for code, _ in warnings}
    if llm_error or "LLM_FAILED" in codes or "LLM_QUOTA_EXCEEDED" in codes:
        return True
    if "PAGES_TRUNCATED" in codes:
        return True
    if not rescued and ("LOW_CONFIDENCE" in codes or "OCR_LOW_QUALITY" in codes or "LLM_NOT_CONFIGURED" in codes):
        return True
    return False


def _metrics(
    deps,
    timer,
    file_type,
    size,
    pages,
    ocr_ms,
    llm_ms,
    llm_used,
    llm_model,
    input_tokens,
    output_tokens,
    questionnaire,
    warnings,
    status,
    method,
    confidence,
):
    return ProcessingMetrics(
        request_id=deps.request_id,
        file_type=file_type,
        file_size_bytes=size,
        pages_or_sheets=pages,
        validation_ms=round(timer.durations.get("validation", 0), 2),
        parsing_ms=round(timer.durations.get("parsing", 0), 2),
        ocr_ms=round(ocr_ms, 2),
        deterministic_extraction_ms=round(timer.durations.get("deterministic", 0), 2),
        llm_ms=round(llm_ms, 2),
        validation_output_ms=round(timer.durations.get("validation_output", 0), 2),
        total_processing_ms=round(timer.total_ms(), 2),
        llm_used=llm_used,
        llm_model=llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        items_detected=questionnaire.total_items or 0,
        warnings_count=len(warnings),
        status=status,
        extraction_method=method,
        confidence_score=confidence,
    )


def _record_failure(deps: ProcessDeps, timer: StageTimer, file_type: str, llm_error: bool = False) -> None:
    deps.metrics.record(
        ProcessingMetrics(
            request_id=deps.request_id,
            file_type=file_type,
            file_size_bytes=0,
            total_processing_ms=round(timer.total_ms(), 2),
            items_detected=0,
            status="failed",
        ),
        llm_error=llm_error,
    )
