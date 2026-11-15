from app.infrastructure.ocr.tesseract_engine import _text_from_data


def test_ocr_keeps_words_on_their_visual_line():
    data = {
        "text": ["1.", "¿Cuál?", "", "A)", "Lima", "2.", "Otra"],
        "conf": ["90", "88", "-1", "80", "82", "91", "90"],
        "block_num": [1, 1, 1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1, 1, 1],
        "line_num": [1, 1, 1, 2, 2, 3, 3],
    }
    text, mean = _text_from_data(data)
    assert text == "1. ¿Cuál?\nA) Lima\n2. Otra"
    assert round(mean, 2) == 86.83
