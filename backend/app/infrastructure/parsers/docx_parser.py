import io

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.core.config import Settings
from app.core.exceptions import AppError
from app.domain.interfaces.parser import ExtractedDocument, TextLine


class DocxParser:
    def parse(
        self,
        data: bytes,
        *,
        settings: Settings,
        force_ocr: bool = False,
    ) -> ExtractedDocument:
        del settings, force_ocr
        try:
            document = Document(io.BytesIO(data))
        except Exception as exc:
            raise AppError(400, "CORRUPTED_FILE", "El DOCX está dañado o no se puede leer.") from exc
        numbering = _numbering_formats(document)
        counters: dict[tuple[str, str], int] = {}
        lines: list[TextLine] = []
        for child in document.element.body.iterchildren():
            if child.tag == qn("w:p"):
                paragraph = Paragraph(child, document)
                text = _numbered_text(paragraph, numbering, counters)
                if text:
                    style = paragraph.style.name if paragraph.style is not None else ""
                    lines.append(TextLine(text, 1, heading=style.startswith(("Title", "Heading"))))
            elif child.tag == qn("w:tbl"):
                table = Table(child, document)
                rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                for row in rows:
                    cells = [cell for cell in row if cell]
                    if cells:
                        lines.append(TextLine(" | ".join(cells), 1))
        return ExtractedDocument(lines, 1, [], [])


def _numbered_text(paragraph: Paragraph, numbering: dict, counters: dict) -> str:
    text = paragraph.text.strip()
    if not text:
        return ""
    num_pr = paragraph._p.find(qn("w:pPr"))
    num_pr = num_pr.find(qn("w:numPr")) if num_pr is not None else None
    if num_pr is None:
        return text
    num_id = _val(num_pr, "w:numId") or "0"
    level = _val(num_pr, "w:ilvl") or "0"
    key = (num_id, level)
    counters[key] = counters.get(key, 0) + 1
    fmt = numbering.get(key, "decimal")
    return f"{_format_label(counters[key], fmt)} {text}"


def _val(element, tag: str) -> str | None:
    node = element.find(qn(tag))
    if node is None:
        return None
    return node.get(qn("w:val"))


def _format_label(number: int, fmt: str) -> str:
    if fmt in {"lowerLetter", "upperLetter"}:
        base = 65 if fmt == "upperLetter" else 97
        value = number
        letters = ""
        while value:
            value, remainder = divmod(value - 1, 26)
            letters = chr(base + remainder) + letters
        return f"{letters})"
    return f"{number}."


def _numbering_formats(document: Document) -> dict[tuple[str, str], str]:
    try:
        numbering = document.part.numbering_part._element
    except Exception:
        return {}
    abstract: dict[str, dict[str, str]] = {}
    for node in numbering.findall(qn("w:abstractNum")):
        abstract_id = node.get(qn("w:abstractNumId"))
        levels = {}
        for level in node.findall(qn("w:lvl")):
            ilvl = level.get(qn("w:ilvl")) or "0"
            fmt = level.find(qn("w:numFmt"))
            levels[ilvl] = fmt.get(qn("w:val")) if fmt is not None else "decimal"
        if abstract_id is not None:
            abstract[abstract_id] = levels
    resolved: dict[tuple[str, str], str] = {}
    for node in numbering.findall(qn("w:num")):
        num_id = node.get(qn("w:numId"))
        abs_node = node.find(qn("w:abstractNumId"))
        if num_id is None or abs_node is None:
            continue
        levels = abstract.get(abs_node.get(qn("w:val")) or "", {})
        for level, fmt in levels.items():
            resolved[(num_id, level)] = fmt or "decimal"
    return resolved
