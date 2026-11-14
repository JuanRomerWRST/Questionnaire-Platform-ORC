from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.dependencies import get_app_settings, get_process_deps
from app.core.config import Settings
from app.core.exceptions import AppError
from app.domain.enums.document_type import DocumentType
from app.infrastructure.ocr.tesseract_engine import TesseractEngine
from app.schemas.document import ExtractOptions
from app.schemas.responses import CapabilitiesResponse, ExtractionResponse, FormatCapability
from app.services.document_service import ProcessDeps, process_document
from app.utils.mime_utils import MIME_TYPES

router = APIRouter(prefix="/documents", tags=["documents"])

_TRUE = {"true", "1", "yes", "si", "sí"}
_FALSE = {"false", "0", "no"}


@router.get("/capabilities", response_model=CapabilitiesResponse)
def capabilities(request: Request, settings: Settings = Depends(get_app_settings)) -> CapabilitiesResponse:
    engine = request.app.state.ocr_engine if getattr(request.app.state, "ready", False) else TesseractEngine(settings)
    formats = [
        FormatCapability(extension=extension, mime_types=MIME_TYPES[document_type])
        for extension, document_type in (
            (".pdf", DocumentType.PDF),
            (".docx", DocumentType.DOCX),
            (".xlsx", DocumentType.XLSX),
            (".png", DocumentType.PNG),
            (".jpg", DocumentType.JPEG),
            (".jpeg", DocumentType.JPEG),
            (".webp", DocumentType.WEBP),
        )
    ]
    return CapabilitiesResponse(
        formats=formats,
        max_upload_size_mb=settings.max_upload_size_mb,
        max_pdf_pages=settings.max_pdf_pages,
        ocr_available=engine.available(),
        llm_available=settings.llm_configured or settings.use_mock_llm,
    )


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    request: Request,
    file: UploadFile | None = File(default=None),
    use_llm: str | None = Form(default=None),
    force_ocr: str | None = Form(default=None),
    deps: ProcessDeps = Depends(get_process_deps),
) -> ExtractionResponse:
    _reject_oversized_request(request, deps.settings)
    if file is None:
        raise AppError(400, "MISSING_FILE", "Debe adjuntar un archivo en el campo file.")
    options = ExtractOptions(use_llm=_optional_bool(use_llm), force_ocr=bool(_optional_bool(force_ocr)))
    return await process_document(file, options, deps)


def _optional_bool(value: str | None) -> bool | None:
    if value is None or value.strip() == "":
        return None
    lowered = value.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise AppError(400, "INVALID_REQUEST", "Los campos use_llm y force_ocr deben ser booleanos.")


def _reject_oversized_request(request: Request, settings: Settings) -> None:
    raw = request.headers.get("content-length")
    if raw and raw.isdigit() and int(raw) > settings.max_upload_bytes + 2 * 1024 * 1024:
        raise AppError(413, "FILE_TOO_LARGE", "El archivo supera el tamaño máximo permitido.")
