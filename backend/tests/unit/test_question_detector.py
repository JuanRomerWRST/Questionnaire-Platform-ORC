from app.domain.interfaces.parser import TextLine
from app.infrastructure.extraction.question_detector import detect_items


def _lines(text: str):
    return [TextLine(line, 1) for line in text.splitlines() if line.strip()]


def test_numbered_styles_and_options():
    dotted = detect_items(_lines("1. ¿Capital de Perú?\nA) Lima\nB) Cusco\n2. ¿Capital de Italia?\na) Roma\nb) Milán"))
    assert [item.numero for item in dotted.items] == [1, 2]
    paren = detect_items(_lines("1) Primera pregunta larga\n2) Segunda pregunta larga"))
    assert [item.numero for item in paren.items] == [1, 2]
    bare = detect_items(_lines("01 Pregunta con cero a la izquierda\nA) Uno\nB) Dos"))
    assert bare.items[0].numero == 1
    assert bare.items[0].options[0].valor == "A"
    restarted = detect_items(_lines("1. Pregunta principal del bloque\nA) Sí\n1) Opción numérica"))
    assert len(restarted.items) == 1
    assert restarted.items[0].options[-1].valor == 1


def test_option_without_space_after_the_letter():
    result = detect_items(_lines("1. ¿Cuánto es 2 + 2?\nA)3\nB) 4\nC)5"))
    assert [option.texto for option in result.items[0].options] == ["3", "4", "5"]


def test_inline_options_and_checkbox():
    result = detect_items(_lines("1. Serie\nA) 18 B) 24 C) 32\n2. Marque\n[x] Sí\n- No"))
    assert [option.texto for option in result.items[0].options] == ["18", "24", "32"]
    assert result.items[1].options[0].marked is True


def test_continuation_across_pages():
    lines = [
        TextLine("1. Esta pregunta", 1),
        TextLine("continúa en la otra página", 2),
        TextLine("A) Sí", 2),
        TextLine("B) No", 2),
    ]
    result = detect_items(lines)
    assert "continúa" in result.items[0].enunciado
    assert len(result.items[0].options) == 2


def test_unnumbered_questions():
    result = detect_items(_lines("¿Cómo se llama?\n¿Dónde vive?"))
    assert len(result.items) == 2
