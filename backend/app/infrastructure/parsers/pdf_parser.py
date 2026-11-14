import io

import pdfplumber
import pymupdf

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.limits import MIN_PAGE_TEXT_CHARS
from app.domain.interfaces.parser import ExtractedDocument, TextLine
from app.infrastructure.parsers.base import split_text_lines, table_rows_to_lines


class PdfParser:
    def parse(
        self,
        data: bytes,
        *,
        settings: Settings,
        force_ocr: bool = False,
    ) -> ExtractedDocument:
        try:
            document = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise AppError(400, "CORRUPTED_FILE", "El PDF está dañado o no se puede leer.") from exc
        if document.needs_pass:
            raise AppError(400, "ENCRYPTED_DOCUMENT", "El PDF está protegido con contraseña.")
        page_count = document.page_count
        if page_count == 0:
            raise AppError(400, "CORRUPTED_FILE", "El PDF no contiene páginas.")
        if page_count > settings.max_pdf_pages:
            raise AppError(400, "DOCUMENT_LIMIT_EXCEEDED", "El PDF supera el máximo de páginas.")

        plumber_pages = _open_plumber(data)
        lines: list[TextLine] = []
        images: list[bytes] = []
        warnings: list[tuple[str, str]] = []
        ocr_budget = settings.max_ocr_pages

        for index, page in enumerate(document):
            page_lines = _page_lines(page, index + 1, plumber_pages, index)
            text_len = sum(len(line.text) for line in page_lines)
            needs_ocr = force_ocr or text_len < MIN_PAGE_TEXT_CHARS
            if needs_ocr:
                if ocr_budget > 0:
                    images.append(_render_page(page))
                    ocr_budget -= 1
                else:
                    warnings.append(
                        ("PAGES_TRUNCATED", "Se omitió el OCR de páginas que superan el límite.")
                    )
            if not needs_ocr or text_len >= MIN_PAGE_TEXT_CHARS:
                lines.extend(page_lines)

        if plumber_pages is not None:
            plumber_pages.close()
        document.close()
        return ExtractedDocument(lines, page_count, images, warnings)


def _open_plumber(data: bytes):
    try:
        return pdfplumber.open(io.BytesIO(data))
    except Exception:
        return None


def _page_lines(page, page_number: int, plumber, index: int) -> list[TextLine]:
    text = page.get_text("text") or ""
    lines = split_text_lines(text, page_number, heading_first=page_number == 1 and bool(text.strip()))
    if plumber is None or index >= len(plumber.pages):
        return lines
    try:
        tables = plumber.pages[index].extract_tables() or []
    except Exception:
        return lines
    table_lines: list[TextLine] = []
    cell_values: set[str] = set()
    for table in tables:
        rows = []
        for row in table:
            cells = [(cell or "").strip() for cell in row]
            if any(cells):
                rows.append(cells)
                cell_values.update(cell for cell in cells if cell)
        table_lines.extend(table_rows_to_lines(rows, page_number))
    if not table_lines:
        return lines
    kept = [line for line in lines if line.text not in cell_values]
    return kept + table_lines


def _render_page(page) -> bytes:
    pixmap = page.get_pixmap(dpi=200, colorspace=pymupdf.csGRAY)
    return pixmap.tobytes("png")
