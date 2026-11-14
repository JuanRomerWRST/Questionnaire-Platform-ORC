import re
import unicodedata
from collections import Counter

from app.domain.interfaces.parser import TextLine

_PAGE_RE = re.compile(
    r"^(page|página|pagina)\s*\d+(\s*(of|de|di)\s*\d+)?$",
    re.IGNORECASE,
)


def normalize_lines(lines: list[TextLine]) -> list[TextLine]:
    cleaned: list[TextLine] = []
    for line in lines:
        text = unicodedata.normalize("NFKC", line.text).replace("\u00a0", " ")
        text = text.replace("•", "-")
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text or _PAGE_RE.match(text):
            continue
        if cleaned and cleaned[-1].text.endswith("-") and text[:1].islower() and cleaned[-1].page == line.page:
            cleaned[-1] = TextLine(cleaned[-1].text[:-1] + text, cleaned[-1].page, cleaned[-1].heading)
            continue
        cleaned.append(TextLine(text, line.page, line.heading))
    return _drop_repeated_chrome(cleaned)


def _drop_repeated_chrome(lines: list[TextLine]) -> list[TextLine]:
    pages = {line.page for line in lines}
    if len(pages) < 3:
        return lines
    counts = Counter(line.text.casefold() for line in lines)
    threshold = max(3, len(pages) * 0.5)
    repeated = {text for text, count in counts.items() if count >= threshold}
    return [line for line in lines if line.text.casefold() not in repeated]
