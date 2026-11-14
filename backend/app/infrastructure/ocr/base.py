from dataclasses import dataclass
from typing import Protocol

from PIL import Image


@dataclass
class OcrResult:
    text: str
    mean_confidence: float


class OCREngine(Protocol):
    def available(self) -> bool: ...

    def recognize(self, image: Image.Image, langs: str) -> OcrResult: ...
