import pytest
from pydantic import ValidationError

from app.domain.enums.question_type import QuestionType
from app.schemas.questionnaire import Questionnaire


def _option(valor, texto="opción"):
    return {"valor": valor, "texto": texto}


def _item(**overrides):
    payload = {
        "numero": 1,
        "enunciado": "¿Cuál es la capital?",
        "tipo": "seleccion_multiple",
        "alternativas": [_option("A", "Lima"), _option("B", "Cusco")],
        "respuesta_correcta": "A",
    }
    payload.update(overrides)
    return payload


def test_total_items_is_derived_when_missing():
    questionnaire = Questionnaire(idioma="es", items=[_item()])
    assert questionnaire.total_items == 1


def test_total_items_must_match_length():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", total_items=2, items=[_item()])


def test_invalid_question_type_is_rejected():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[_item(tipo="ensayo")])


def test_duplicate_numbers_are_rejected():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[_item(), _item()])


def test_descending_numbers_are_rejected():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[_item(numero=2), _item(numero=1)])


def test_none_alternatives_become_empty_list_for_open_questions():
    questionnaire = Questionnaire(
        idioma="it",
        items=[_item(tipo="desarrollo", alternativas=None, respuesta_correcta=None)],
    )
    assert questionnaire.items[0].alternativas == []


def test_open_question_rejects_options():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[_item(tipo="desarrollo")])


def test_true_false_requires_two_options():
    with pytest.raises(ValidationError):
        Questionnaire(
            idioma="en",
            items=[
                _item(
                    tipo="verdadero_falso",
                    alternativas=[_option("V", "Verdadero")],
                    respuesta_correcta=None,
                )
            ],
        )


def test_answer_must_belong_to_options():
    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[_item(respuesta_correcta="Z")])


def test_bool_valor_is_rejected():
    with pytest.raises(ValidationError):
        Questionnaire(
            idioma="es",
            items=[
                _item(
                    tipo="escala_likert",
                    alternativas=[_option(True, "Sí"), _option(0, "No")],
                    respuesta_correcta=None,
                )
            ],
        )


def test_matching_pairs_must_reference_existing_values():
    item = _item(
        tipo="emparejamiento",
        alternativas=[
            _option(1, "Roma"),
            _option("A", "Italia"),
            _option(2, "Lima"),
            _option("B", "Perú"),
        ],
        respuesta_correcta="1-A,2-B",
    )
    questionnaire = Questionnaire(idioma="es", items=[item])
    assert questionnaire.items[0].tipo == QuestionType.EMPAREJAMIENTO

    with pytest.raises(ValidationError):
        Questionnaire(idioma="es", items=[{**item, "respuesta_correcta": "1-Z"}])


def test_untitled_fallback_and_language_codes():
    questionnaire = Questionnaire(titulo="   ", idioma="UND", items=[])
    assert questionnaire.titulo == "Cuestionario sin título"
    assert questionnaire.idioma == "und"
    assert questionnaire.total_items == 0

    with pytest.raises(ValidationError):
        Questionnaire(idioma="español", items=[])


def test_numbering_gaps_are_allowed():
    questionnaire = Questionnaire(idioma="en", items=[_item(numero=1), _item(numero=3)])
    assert [item.numero for item in questionnaire.items] == [1, 3]
