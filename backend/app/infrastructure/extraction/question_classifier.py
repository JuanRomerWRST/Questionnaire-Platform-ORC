import re
from dataclasses import dataclass

from app.domain.entities.questionnaire import DraftItem, DraftOption
from app.domain.enums.question_type import QuestionType
from app.infrastructure.extraction.regex_patterns import (
    LIKERT_VOCAB,
    OPEN_KEYWORDS,
    TRUE_FALSE_MARKER,
    VF_VOCAB,
)

_VF_BY_LANGUAGE = {
    "es": (("V", "Verdadero"), ("F", "Falso")),
    "en": (("T", "True"), ("F", "False")),
    "it": (("V", "Vero"), ("F", "Falso")),
}


@dataclass
class Classification:
    tipo: QuestionType
    conflicts: list[str]


def classify(item: DraftItem) -> Classification:
    if item.type_hint in {tipo.value for tipo in QuestionType}:
        return Classification(QuestionType(item.type_hint), [])
    if item.matching or _is_matching(item):
        return Classification(QuestionType.EMPAREJAMIENTO, [])
    conflicts: list[str] = []
    vf = _is_true_false(item)
    likert_ratio = _likert_ratio(item)
    if OPEN_KEYWORDS.search(item.enunciado) and item.options:
        conflicts.append("open_with_options")
    if 0.30 <= likert_ratio < 0.60:
        conflicts.append("ambiguous_likert")
    if TRUE_FALSE_MARKER.search(item.enunciado) and len(item.options) > 2:
        conflicts.append("vf_with_extra_options")
    if vf:
        return Classification(QuestionType.VERDADERO_FALSO, conflicts)
    if _is_likert(item, likert_ratio):
        return Classification(QuestionType.ESCALA_LIKERT, conflicts)
    labeled = [option for option in item.options if option.texto.strip()]
    if len(labeled) >= 2:
        return Classification(QuestionType.SELECCION_MULTIPLE, conflicts)
    if len(labeled) == 1:
        conflicts.append("single_option")
        return Classification(QuestionType.DESARROLLO, conflicts)
    return Classification(QuestionType.DESARROLLO, conflicts)


def assign_values(item: DraftItem, language: str) -> None:
    marker = TRUE_FALSE_MARKER.search(item.enunciado)
    if item.tipo == QuestionType.VERDADERO_FALSO and marker and len(item.options) != 2:
        pair = _VF_BY_LANGUAGE.get(language, _VF_BY_LANGUAGE["es"])
        item.options = [DraftOption(texto=text, valor=valor) for valor, text in pair]
    if item.tipo == QuestionType.DESARROLLO:
        if len(item.options) == 1:
            item.options = []
        return
    if item.tipo == QuestionType.ESCALA_LIKERT:
        _assign_likert(item)
        return
    if item.tipo == QuestionType.SELECCION_MULTIPLE:
        _assign_letters(item)
        return
    if item.tipo == QuestionType.EMPAREJAMIENTO:
        _assign_matching(item)


def _is_matching(item: DraftItem) -> bool:
    integers = [option for option in item.options if isinstance(option.valor, int)]
    letters = [option for option in item.options if isinstance(option.valor, str)]
    return len(integers) >= 1 and len(letters) >= 1 and len(item.options) >= 2 and item.matching


def _is_true_false(item: DraftItem) -> bool:
    if len(item.options) == 2 and all(option.texto.casefold().strip() in VF_VOCAB for option in item.options):
        return True
    return bool(TRUE_FALSE_MARKER.search(item.enunciado) and len(item.options) <= 2)


def _likert_ratio(item: DraftItem) -> float:
    if not item.options:
        return 0
    hits = sum(1 for option in item.options if option.texto.casefold().strip() in LIKERT_VOCAB)
    return hits / len(item.options)


def _is_likert(item: DraftItem, ratio: float) -> bool:
    if len(item.options) < 3:
        return False
    if any(isinstance(option.valor, str) and str(option.valor).isalpha() for option in item.options):
        return False
    if ratio >= 0.60:
        return True
    values = [option.valor for option in item.options]
    if all(isinstance(value, int) for value in values):
        numbers = [int(value) for value in values if isinstance(value, int)]
        return numbers == list(range(numbers[0], numbers[0] + len(numbers)))
    return all(re.fullmatch(r"\d+", option.texto.strip()) for option in item.options)


def _assign_likert(item: DraftItem) -> None:
    if all(isinstance(option.valor, int) for option in item.options):
        return
    for index, option in enumerate(item.options):
        if isinstance(option.valor, int):
            continue
        found = re.match(r"^(\d+)$", option.texto.strip())
        option.valor = int(found.group(1)) if found else index


def _assign_letters(item: DraftItem) -> None:
    for index, option in enumerate(item.options):
        if option.valor is None:
            option.valor = chr(65 + index)


def _assign_matching(item: DraftItem) -> None:
    for option in item.options:
        if isinstance(option.valor, str):
            option.valor = option.valor.upper()
