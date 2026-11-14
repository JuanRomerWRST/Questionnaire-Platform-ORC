from dataclasses import dataclass, field

from app.domain.entities.questionnaire import DraftItem
from app.domain.enums.question_type import QuestionType
from app.infrastructure.extraction.question_detector import DetectionResult


@dataclass
class ConfidenceReport:
    score: float
    warnings: list[tuple[str, str]] = field(default_factory=list)
    needs_llm: bool = False


def score_extraction(
    items: list[DraftItem],
    detection: DetectionResult,
    *,
    ocr_used: bool,
    ocr_confidence: float | None,
    threshold: float,
) -> ConfidenceReport:
    warnings: list[tuple[str, str]] = []
    if not items:
        return ConfidenceReport(0, warnings, needs_llm=True)
    penalty = 0.0
    numbers = [item.numero for item in items]
    if numbers != sorted(numbers) or len(numbers) != len(set(numbers)) or _has_gap(numbers):
        penalty += 0.15
        if _has_gap(numbers):
            warnings.append(("NUMBERING_GAP", "La numeración de los ítems tiene saltos."))
    empty = sum(1 for item in items if not item.enunciado.strip())
    if empty:
        penalty += 0.20 * (empty / len(items))
    weak_options = sum(
        1
        for item in items
        if item.tipo in {QuestionType.SELECCION_MULTIPLE, QuestionType.ESCALA_LIKERT, QuestionType.VERDADERO_FALSO}
        and len(item.options) < 2
    )
    if weak_options:
        penalty += 0.15 * (weak_options / len(items))
    if detection.total_chars:
        ratio = detection.orphan_chars / detection.total_chars
        if ratio > 0.15:
            penalty += 0.20
            warnings.append(("ORPHAN_TEXT", "Quedó texto sin asociar a un ítem."))
        elif ratio > 0.05:
            penalty += 0.10
            warnings.append(("ORPHAN_TEXT", "Hay fragmentos de texto sin clasificar."))
    conflicts = sum(1 for item in items if item.conflicts)
    if conflicts:
        penalty += min(0.20, 0.10 * (conflicts / len(items)))
        warnings.append(("CLASSIFICATION_CONFLICT", "Algún ítem tiene una clasificación ambigua."))
    if ocr_used and detection.total_chars < 200:
        penalty += 0.40
        warnings.append(("OCR_LOW_QUALITY", "El OCR obtuvo poco texto."))
    if ocr_used and ocr_confidence is not None and ocr_confidence < 60:
        penalty += 0.20
        warnings.append(("OCR_LOW_QUALITY", "La confianza media del OCR es baja."))
    value = max(0.0, min(1.0, 1 - penalty))
    needs_llm = value < threshold or (ocr_used and detection.total_chars < 200)
    if needs_llm and not any(code == "LOW_CONFIDENCE" for code, _ in warnings):
        warnings.append(("LOW_CONFIDENCE", "La extracción determinística no es suficientemente confiable."))
    return ConfidenceReport(round(value, 2), warnings, needs_llm)


def _has_gap(numbers: list[int]) -> bool:
    return any(right - left > 1 for left, right in zip(numbers, numbers[1:], strict=False))
