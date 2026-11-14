import io

from openpyxl import load_workbook

from app.core.config import Settings
from app.core.exceptions import AppError
from app.domain.interfaces.parser import ExtractedDocument, TextLine

_NUMBER = {"n", "nº", "numero", "número", "number", "#", "item"}
_PROMPT = {
    "pregunta",
    "enunciado",
    "question",
    "statement",
    "domanda",
    "testo",
    "item",
}
_TYPE = {"tipo", "type"}
_OPTIONS = {"opciones", "alternativas", "options", "opzioni", "choices"}
_ANSWER = {
    "respuesta",
    "respuesta_correcta",
    "answer",
    "correct",
    "risposta",
    "risposta_corretta",
    "soluzione",
    "clave",
}


class XlsxParser:
    def parse(
        self,
        data: bytes,
        *,
        settings: Settings,
        force_ocr: bool = False,
    ) -> ExtractedDocument:
        del force_ocr
        try:
            workbook = load_workbook(
                io.BytesIO(data),
                read_only=True,
                data_only=True,
                keep_links=False,
            )
        except Exception as exc:
            raise AppError(400, "CORRUPTED_FILE", "El XLSX está dañado o no se puede leer.") from exc
        if len(workbook.sheetnames) > settings.max_xlsx_sheets:
            workbook.close()
            raise AppError(400, "DOCUMENT_LIMIT_EXCEEDED", "El libro supera el máximo de hojas.")
        lines: list[TextLine] = []
        warnings: list[tuple[str, str]] = []
        sheet_count = len(workbook.sheetnames)
        for sheet_index, name in enumerate(workbook.sheetnames, start=1):
            sheet = workbook[name]
            rows = _limited_rows(sheet, settings.max_xlsx_rows_per_sheet)
            if len(rows) >= settings.max_xlsx_rows_per_sheet:
                warnings.append(("PAGES_TRUNCATED", f"La hoja {name} se truncó por el límite de filas."))
            lines.extend(_sheet_lines(name, rows, sheet_index))
        workbook.close()
        return ExtractedDocument(lines, sheet_count, warnings=warnings)


def _limited_rows(sheet, limit: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for index, row in enumerate(sheet.iter_rows(values_only=True)):
        if index >= limit:
            break
        values = ["" if cell is None else str(cell).strip() for cell in row]
        if any(values):
            rows.append(values)
    return rows


def _sheet_lines(name: str, rows: list[list[str]], page: int) -> list[TextLine]:
    if not rows:
        return []
    header = [cell.casefold() for cell in rows[0]]
    if not _has_known_header(header):
        return [TextLine(" | ".join(cell for cell in row if cell), page) for row in rows]
    indexes = {label: header.index(label) for label in header if label}
    lines = [TextLine(name, page, heading=True)]
    for row in rows[1:]:
        lines.extend(_canonical_row(row, indexes, page))
    return lines


def _has_known_header(header: list[str]) -> bool:
    known = _NUMBER | _PROMPT | _TYPE | _OPTIONS | _ANSWER
    return any(cell in known or cell.startswith("opcion_") or cell.startswith("option_") for cell in header)


def _canonical_row(row: list[str], indexes: dict[str, int], page: int) -> list[TextLine]:
    def cell(names: set[str]) -> str:
        for name in names:
            index = indexes.get(name)
            if index is not None and index < len(row):
                return row[index]
        return ""

    number = cell(_NUMBER) or ""
    prompt = cell(_PROMPT)
    if not prompt:
        flat = " | ".join(value for value in row if value)
        return [TextLine(flat, page)] if flat else []
    prefix = f"{number}. " if number else ""
    lines = [TextLine(f"{prefix}{prompt}", page)]
    options = cell(_OPTIONS)
    if options:
        chunks = [part.strip() for part in _split_options(options) if part.strip()]
        for index, option in enumerate(chunks):
            if option[:2].rstrip(".)").isalpha() and option[1:2] in {")", ".", ":"}:
                lines.append(TextLine(option, page))
            else:
                lines.append(TextLine(f"{chr(65 + index)}) {option}", page))
    else:
        for letter in "abcdefgh":
            for key in (f"opcion_{letter}", f"option_{letter}", f"opzione_{letter}", letter):
                value = indexes.get(key)
                if value is not None and value < len(row) and row[value]:
                    lines.append(TextLine(f"{letter.upper()}) {row[value]}", page))
                    break
    kind = cell(_TYPE)
    if kind:
        lines.append(TextLine(f"Tipo: {kind}", page))
    answer = cell(_ANSWER)
    if answer:
        lines.append(TextLine(f"Respuesta correcta: {answer}", page))
    return lines


def _split_options(value: str) -> list[str]:
    if "\n" in value:
        return value.splitlines()
    if ";" in value:
        return value.split(";")
    if "|" in value:
        return value.split("|")
    return [value]
