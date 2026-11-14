import re

from langdetect import DetectorFactory, LangDetectException, detect_langs

from app.core.limits import LANGUAGE_MIN_LETTERS, LANGUAGE_MIN_PROBABILITY

DetectorFactory.seed = 0


def detect_language(text: str) -> tuple[str, bool]:
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñÀÈÌÒÙàèìòù]", "", text)
    if len(letters) < LANGUAGE_MIN_LETTERS:
        return "und", True
    try:
        candidates = detect_langs(text)
    except LangDetectException:
        return "und", True
    if not candidates or candidates[0].prob < LANGUAGE_MIN_PROBABILITY:
        return "und", True
    return candidates[0].lang, False
