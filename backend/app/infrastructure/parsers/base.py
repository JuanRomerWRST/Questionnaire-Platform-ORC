from app.domain.interfaces.parser import TextLine


def split_text_lines(text: str, page: int, *, heading_first: bool = False) -> list[TextLine]:
    lines: list[TextLine] = []
    for index, raw in enumerate(text.splitlines()):
        cleaned = raw.strip()
        if cleaned:
            lines.append(TextLine(cleaned, page, heading=heading_first and index == 0))
    return lines


def table_rows_to_lines(rows: list[list[str | None]], page: int) -> list[TextLine]:
    lines: list[TextLine] = []
    for row in rows:
        cells = [cell.strip() for cell in row if cell and cell.strip()]
        if cells:
            lines.append(TextLine(" | ".join(cells), page))
    return lines
