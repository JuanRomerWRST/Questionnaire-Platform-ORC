from app.domain.entities.questionnaire import DraftItem, DraftOption
from app.domain.enums.question_type import QuestionType
from app.infrastructure.extraction.language_detector import detect_language
from app.infrastructure.extraction.question_classifier import classify
from app.services.classification_service import classify_items


def _item(enunciado, options, **kwargs):
    return DraftItem(
        numero=1,
        enunciado=enunciado,
        options=[DraftOption(texto=text, valor=valor) for valor, text in options],
        **kwargs,
    )


def test_five_types():
    samples = [
        _item("Me siento bien", [(None, "Nunca"), (None, "A veces"), (None, "Siempre")]),
        _item("¿Color?", [("A", "Rojo"), ("B", "Azul")]),
        _item("El hielo es sólido. (V/F)", []),
        _item("Describa su día", []),
        _item("Relaciona", [(1, "Roma"), ("A", "Italia")], matching=True),
    ]
    types = [classify(item).tipo for item in samples]
    assert types == [
        QuestionType.ESCALA_LIKERT,
        QuestionType.SELECCION_MULTIPLE,
        QuestionType.VERDADERO_FALSO,
        QuestionType.DESARROLLO,
        QuestionType.EMPAREJAMIENTO,
    ]


def test_explicit_answer_and_missing_answer():
    item = _item("¿Suma?", [("A", "3"), ("B", "4")], raw_answer="B")
    other = _item("¿Suma?", [("A", "3"), ("B", "4")])
    warnings = classify_items([item, other], "es", {})
    assert warnings == []
    assert item.raw_answer == "B"
    assert other.raw_answer is None


def test_invalid_answer_is_cleared():
    item = _item("¿Suma?", [("A", "3"), ("B", "4")], raw_answer="Z")
    warnings = classify_items([item], "es", {})
    assert warnings[0][0] == "ANSWER_NOT_IN_OPTIONS"
    assert item.raw_answer is None


def test_languages():
    spanish = "Este cuestionario pregunta por hábitos de estudio y concentración durante la semana."
    english = "This questionnaire asks about study habits and concentration during the week."
    italian = "Questo questionario chiede delle abitudini di studio e della concentrazione settimanale."
    assert detect_language(spanish)[0] == "es"
    assert detect_language(english)[0] == "en"
    assert detect_language(italian)[0] == "it"
    assert detect_language("123 456")[0] == "und"
