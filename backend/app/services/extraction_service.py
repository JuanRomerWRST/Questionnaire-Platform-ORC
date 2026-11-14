import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.domain.entities.questionnaire import DraftItem
from app.domain.interfaces.parser import ExtractedDocument, TextLine
from app.infrastructure.extraction.confidence import ConfidenceReport, score_extraction
from app.infrastructure.extraction.language_detector import detect_language
from app.infrastructure.extraction.question_detector import detect_items
from app.infrastructure.extraction.text_normalizer import normalize_lines
from app.schemas.questionnaire import UNTITLED, Questionnaire
from app.services.classification_service import classify_items

_INSTRUCTION = re.compile(
    r"^(instrucciones|instructions|istruzioni|nombre|name|fecha|date)\b",
    re.IGNORECASE,
)


@dataclass
class DeterministicResult:
    questionnaire: Questionnaire | None
    warnings: list[tuple[str, str]] = field(default_factory=list)
    confidence: ConfidenceReport = field(default_factory=lambda: ConfidenceReport(0, [], True))
    text: str = ""
    ocr_used: bool = False


def run_deterministic(
    document: ExtractedDocument,
    *,
    threshold: float,
    ocr_used: bool,
    ocr_confidence: float | None,
) -> DeterministicResult:
    lines = normalize_lines(document.lines)
    detection = detect_items(lines)
    text = "\n".join(line.text for line in lines)
    corpus = "\n".join(
        item.enunciado + " " + " ".join(option.texto for option in item.options) for item in detection.items
    )
    language, uncertain = detect_language(corpus or text)
    warnings = list(document.warnings)
    if uncertain:
        warnings.append(("LANGUAGE_UNDETERMINED", "No se pudo determinar el idioma con suficiente confianza."))
    answer_warnings = classify_items(detection.items, language if language != "und" else "es", detection.answer_key)
    warnings.extend(answer_warnings)
    _dedupe_numbers(detection.items)
    confidence = score_extraction(
        detection.items,
        detection,
        ocr_used=ocr_used,
        ocr_confidence=ocr_confidence,
        threshold=threshold,
    )
    if any(code == "ANSWER_NOT_IN_OPTIONS" for code, _ in answer_warnings):
        confidence.score = round(max(0.0, confidence.score - 0.05), 2)
    warnings.extend(confidence.warnings)
    questionnaire = _build(choose_title(lines, detection.preamble), language, detection.items)
    if questionnaire is None and detection.items:
        warnings.append(("LOW_CONFIDENCE", "Los ítems detectados no pasaron la validación del contrato."))
    return DeterministicResult(questionnaire, _unique(warnings), confidence, text, ocr_used)


def choose_title(lines: list[TextLine], preamble: list[str]) -> str:
    candidates = [line.text for line in lines if line.heading] + preamble
    for text in candidates:
        if 3 <= len(text) <= 120 and not _INSTRUCTION.match(text):
            return text
    return UNTITLED


def _build(title: str, language: str, items: list[DraftItem]) -> Questionnaire | None:
    payload = []
    for item in items:
        if item.tipo is None:
            continue
        options = [
            {"valor": option.valor, "texto": option.texto}
            for option in item.options
            if option.valor is not None and option.texto.strip()
        ]
        payload.append(
            {
                "numero": item.numero,
                "enunciado": item.enunciado,
                "tipo": item.tipo.value,
                "alternativas": options,
                "respuesta_correcta": _answer(item),
            }
        )
    try:
        return Questionnaire.model_validate({"titulo": title, "idioma": language, "items": payload})
    except ValidationError:
        return None


def _answer(item: DraftItem):
    if not item.raw_answer:
        return None
    if item.raw_answer.isdigit() and any(isinstance(option.valor, int) for option in item.options):
        return int(item.raw_answer)
    return item.raw_answer


def _dedupe_numbers(items: list[DraftItem]) -> None:
    seen: set[int] = set()
    next_number = 1
    for item in items:
        if item.numero in seen or item.numero < next_number:
            while next_number in seen:
                next_number += 1
            item.numero = next_number
        seen.add(item.numero)
        next_number = item.numero + 1


def _unique(warnings: list[tuple[str, str]]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for warning in warnings:
        if warning not in found:
            found.append(warning)
    return found
