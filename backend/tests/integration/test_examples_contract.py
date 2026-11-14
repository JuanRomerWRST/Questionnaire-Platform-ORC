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
PARSERS = {".pdf": PdfParser, ".docx": DocxParser, ".xlsx": XlsxParser}


def _deterministic_examples():
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    return [case["file"] for case in cases if case["mode"] == "deterministic"]


@pytest.mark.parametrize("name", _deterministic_examples())
def test_example_outputs_match_the_pipeline(name):
    data = (ROOT / "input" / name).read_bytes()
    expected = json.loads((ROOT / "output" / Path(name).with_suffix(".json").name).read_text(encoding="utf-8"))
    parsed = PARSERS[Path(name).suffix]().parse(data, settings=get_settings())
    result = run_deterministic(parsed, threshold=0.7, ocr_used=False, ocr_confidence=None)
    assert result.questionnaire is not None
    assert result.questionnaire.model_dump() == expected


def test_photo_output_matches_the_contract():
    payload = json.loads((ROOT / "output" / "sample_questionnaire_photo.json").read_text(encoding="utf-8"))
    questionnaire = Questionnaire.model_validate(payload)
    assert questionnaire.total_items == len(questionnaire.items)
    assert questionnaire.total_items > 0
