import io
import zipfile

import pytest

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.utils.mime_utils import sniff_document_type
from tests.fixtures.builders import SPANISH_LINES, docx_bytes, image_bytes, pdf_bytes, xlsx_bytes


def _check(data: bytes, extension: str):
    return sniff_document_type(data, extension, get_settings())


@pytest.mark.parametrize(
    ("builder", "extension"),
    [
        (lambda: pdf_bytes(SPANISH_LINES), ".pdf"),
        (lambda: docx_bytes(["Hola"]), ".docx"),
        (lambda: xlsx_bytes({"Hoja": [["n", "pregunta"], ["1", "¿Qué?"]]}), ".xlsx"),
        (lambda: image_bytes(["Hola"]), ".png"),
    ],
)
def test_supported_signatures(builder, extension):
    assert _check(builder(), extension).value


def test_empty_file_is_rejected_by_reader():
    from app.utils.file_utils import read_upload_limited

    class Upload:
        async def read(self, _size):
            return b""

    with pytest.raises(AppError) as caught:
        import asyncio

        asyncio.run(read_upload_limited(Upload(), 100))
    assert caught.value.code == "EMPTY_FILE"


def test_corrupt_pdf_is_rejected():
    from app.infrastructure.parsers.pdf_parser import PdfParser

    with pytest.raises(AppError) as caught:
        PdfParser().parse(b"%PDF-1.7 this is not a real pdf body", settings=get_settings())
    assert caught.value.code == "CORRUPTED_FILE"


def test_extension_mismatch():
    with pytest.raises(AppError) as caught:
        _check(image_bytes(["Hola"]), ".pdf")
    assert caught.value.code == "MIME_MISMATCH"


def test_executable_is_rejected():
    with pytest.raises(AppError) as caught:
        _check(b"MZ\x90\x00", ".exe")
    assert caught.value.code == "UNSUPPORTED_FORMAT"


def test_macro_docx_is_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<xml/>")
        archive.writestr("word/vbaProject.bin", b"macro")
    with pytest.raises(AppError) as caught:
        _check(buffer.getvalue(), ".docx")
    assert caught.value.code == "UNSAFE_ARCHIVE"


def test_zip_bomb_is_rejected(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "max_zip_uncompressed_mb", 1)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", b"0" * (2 * 1024 * 1024))
    with pytest.raises(AppError) as caught:
        sniff_document_type(buffer.getvalue(), ".docx", settings)
    assert caught.value.code == "UNSAFE_ARCHIVE"
