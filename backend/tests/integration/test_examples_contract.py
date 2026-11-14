import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.infrastructure.parsers.docx_parser import DocxParser
from app.infrastructure.parsers.pdf_parser import PdfParser
from app.infrastructure.parsers.xlsx_parser import XlsxParser
from app.schemas.questionnaire import Questionnaire
from app.services.extraction_service import run_deterministic

ROOT = Path(__file__).resolve().parents[3] / "examples"


@pytest.mark.parametrize(
    ("name", "parser"),
    [
        ("sample_questionnaire_es.pdf", PdfParser),
        ("sample_questionnaire_it.docx", DocxParser),
        ("sample_questionnaire_en.xlsx", XlsxParser),
    ],
)
def test_example_outputs_match_the_pipeline(name, parser):
    data = (ROOT / "input" / name).read_bytes()
    expected = json.loads((ROOT / "output" / name.replace(Path(name).suffix, ".json")).read_text(encoding="utf-8"))
    parsed = parser().parse(data, settings=get_settings())
    result = run_deterministic(parsed, threshold=0.7, ocr_used=False, ocr_confidence=None)
    assert result.questionnaire is not None
    assert result.questionnaire.model_dump() == expected


def test_photo_output_matches_the_contract():
    payload = json.loads((ROOT / "output" / "sample_questionnaire_photo.json").read_text(encoding="utf-8"))
    questionnaire = Questionnaire.model_validate(payload)
    assert questionnaire.total_items == len(questionnaire.items)
    assert questionnaire.total_items > 0
