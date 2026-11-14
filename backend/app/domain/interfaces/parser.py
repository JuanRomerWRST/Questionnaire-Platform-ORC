from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import Settings


@dataclass
class TextLine:
    text: str
    page: int
    heading: bool = False


@dataclass
class ExtractedDocument:
    lines: list[TextLine]
    pages_or_sheets: int
    pending_ocr_images: list[bytes] = field(default_factory=list)
    warnings: list[tuple[str, str]] = field(default_factory=list)
    ocr_confidences: list[float] = field(default_factory=list)


class DocumentParser(Protocol):
    def parse(
        self,
        data: bytes,
        *,
        settings: Settings,
        force_ocr: bool = False,
    ) -> ExtractedDocument: ...
