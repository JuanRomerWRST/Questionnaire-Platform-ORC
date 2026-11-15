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
    data = pytesseract.image_to_data(
        image,
        lang=langs,
        config="--psm 6",
        output_type=pytesseract.Output.DICT,
    )
    return _text_from_data(data)


def _text_from_data(data: dict) -> tuple[str, float]:
    words = data.get("text", [])
    confs = data.get("conf", [])
    blocks = data.get("block_num", [])
    paragraphs = data.get("par_num", [])
    line_nums = data.get("line_num", [])
    lines: list[list[str]] = []
    current: tuple[int, int, int] | None = None
    confidences: list[float] = []
    for index, word in enumerate(words):
        try:
            score = float(confs[index])
        except (TypeError, ValueError, IndexError):
            continue
        token = str(word).strip()
        if score < 0 or not token:
            continue
        key = (
            int(blocks[index]) if index < len(blocks) else 0,
            int(paragraphs[index]) if index < len(paragraphs) else 0,
            int(line_nums[index]) if index < len(line_nums) else 0,
        )
        if key != current:
            lines.append([])
            current = key
        lines[-1].append(token)
        confidences.append(score)
    mean = sum(confidences) / len(confidences) if confidences else 0.0
    return "\n".join(" ".join(line) for line in lines), mean


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
