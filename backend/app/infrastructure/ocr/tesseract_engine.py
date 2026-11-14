import shutil

import pytesseract
from PIL import Image

from app.core.config import Settings
from app.core.limits import OCR_LOW_CONFIDENCE
from app.infrastructure.ocr.base import OcrResult


class TesseractEngine:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def available(self) -> bool:
        if not self._settings.ocr_enabled:
            return False
        command = self._settings.tesseract_cmd or "tesseract"
        return shutil.which(command) is not None

    def recognize(self, image: Image.Image, langs: str) -> OcrResult:
        text, confidence = _read(image, langs)
        if confidence < OCR_LOW_CONFIDENCE:
            rotated = _rotate_from_osd(image)
            if rotated is not None:
                text, confidence = _read(rotated, langs)
        return OcrResult(text.strip(), confidence)


def _read(image: Image.Image, langs: str) -> tuple[str, float]:
    data = pytesseract.image_to_data(image, lang=langs, output_type=pytesseract.Output.DICT)
    words: list[str] = []
    confidences: list[float] = []
    for word, conf in zip(data.get("text", []), data.get("conf", []), strict=False):
        try:
            score = float(conf)
        except (TypeError, ValueError):
            continue
        if score < 0 or not str(word).strip():
            continue
        words.append(str(word))
        confidences.append(score)
    mean = sum(confidences) / len(confidences) if confidences else 0
    return " ".join(words), mean


def _rotate_from_osd(image: Image.Image) -> Image.Image | None:
    try:
        osd = pytesseract.image_to_osd(image)
    except Exception:
        return None
    angle = 0
    for line in osd.splitlines():
        if "Rotate:" in line:
            angle = int(line.split(":")[1].strip() or "0")
    if angle in {0, 360}:
        return None
    return image.rotate(-angle, expand=True)
