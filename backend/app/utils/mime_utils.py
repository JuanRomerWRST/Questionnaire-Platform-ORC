import io
import zipfile

from app.core.config import Settings
from app.core.exceptions import AppError
from app.domain.enums.document_type import DocumentType

EXT_TO_TYPE: dict[str, DocumentType] = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".xlsx": DocumentType.XLSX,
    ".png": DocumentType.PNG,
    ".jpg": DocumentType.JPEG,
    ".jpeg": DocumentType.JPEG,
    ".webp": DocumentType.WEBP,
}

MIME_TYPES: dict[DocumentType, list[str]] = {
    DocumentType.PDF: ["application/pdf"],
    DocumentType.DOCX: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    DocumentType.XLSX: ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    DocumentType.PNG: ["image/png"],
    DocumentType.JPEG: ["image/jpeg"],
    DocumentType.WEBP: ["image/webp"],
}


def sniff_document_type(data: bytes, extension: str, settings: Settings) -> DocumentType:
    ext = extension.lower()
    if ext not in EXT_TO_TYPE:
        raise AppError(
            415,
            "UNSUPPORTED_FORMAT",
            "El formato no está soportado. Use PDF, DOCX, XLSX, PNG, JPG o WEBP.",
        )
    expected = EXT_TO_TYPE[ext]
    detected = _detect_magic(data)
    if detected is None:
        raise AppError(400, "CORRUPTED_FILE", "No se reconoció el contenido del archivo.")
    if detected != expected:
        raise AppError(415, "MIME_MISMATCH", "La extensión no coincide con el contenido real.")
    if expected in {DocumentType.DOCX, DocumentType.XLSX}:
        inspect_ooxml(data, expected, settings)
    return expected


def inspect_ooxml(data: bytes, expected: DocumentType, settings: Settings) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise AppError(400, "CORRUPTED_FILE", "El documento Office está dañado.") from exc
    infos = archive.infolist()
    if len(infos) > settings.max_zip_entries:
        raise AppError(400, "UNSAFE_ARCHIVE", "El archivo comprimido tiene demasiadas entradas.")
    uncompressed = sum(info.file_size for info in infos)
    compressed = max(sum(info.compress_size for info in infos), 1)
    limit = settings.max_zip_uncompressed_mb * 1024 * 1024
    if uncompressed > limit or uncompressed / compressed > settings.max_zip_ratio:
        raise AppError(400, "UNSAFE_ARCHIVE", "El archivo parece un zip bomb o supera el tamaño seguro.")
    names = {info.filename.replace("\\", "/") for info in infos}
    if any(name.endswith("vbaProject.bin") for name in names):
        raise AppError(400, "UNSAFE_ARCHIVE", "No se aceptan documentos con macros.")
    if "[Content_Types].xml" in names and b"macroEnabled" in archive.read("[Content_Types].xml"):
        raise AppError(400, "UNSAFE_ARCHIVE", "No se aceptan documentos con macros.")
    if expected == DocumentType.DOCX and "word/document.xml" not in names:
        raise AppError(400, "CORRUPTED_FILE", "El DOCX no contiene el documento principal.")
    if expected == DocumentType.XLSX and "xl/workbook.xml" not in names:
        raise AppError(400, "CORRUPTED_FILE", "El XLSX no contiene el libro principal.")


def _detect_magic(data: bytes) -> DocumentType | None:
    if data.startswith(b"%PDF-"):
        return DocumentType.PDF
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return DocumentType.PNG
    if data.startswith(b"\xff\xd8\xff"):
        return DocumentType.JPEG
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return DocumentType.WEBP
    if data.startswith(b"PK\x03\x04"):
        return _office_kind(data)
    return None


def _office_kind(data: bytes) -> DocumentType | None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return None
    names = set(archive.namelist())
    if "word/document.xml" in names:
        return DocumentType.DOCX
    if "xl/workbook.xml" in names:
        return DocumentType.XLSX
    return None
