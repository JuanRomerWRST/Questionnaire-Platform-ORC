from app.domain.entities.questionnaire import DraftItem
from app.infrastructure.extraction.answer_detector import resolve_answers
from app.infrastructure.extraction.question_classifier import assign_values, classify


def classify_items(items: list[DraftItem], language: str, answer_key: dict[int, str]) -> list[tuple[str, str]]:
    for item in items:
        classified = classify(item)
        item.tipo = classified.tipo
        item.conflicts = classified.conflicts
        assign_values(item, language)
    return resolve_answers(items, answer_key)
