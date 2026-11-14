"""Genera los cuestionarios sintéticos de examples/ a partir del pipeline real."""

import json
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.parsers.docx_parser import DocxParser
from app.infrastructure.parsers.pdf_parser import PdfParser
from app.infrastructure.parsers.xlsx_parser import XlsxParser
from app.services.extraction_service import run_deterministic
from tests.fixtures.builders import SPANISH_LINES, docx_bytes, image_bytes, pdf_bytes, xlsx_bytes

ROOT = Path(__file__).resolve().parents[3] / "examples"
ITALIAN = [
    "Questionario di esempio",
    "1. Mi preoccupo eccessivamente per cose di poca importanza.",
    "Mai",
    "A volte",
    "Spesso",
    "Sempre",
    "2. Quale numero completa la serie: 2, 4, 8, 16?",
    "A) 18",
    "B) 24",
    "C) 32",
    "Risposta corretta: C",
    "3. Descriva una situazione recente in cui si è sentito sotto pressione.",
    "4. Abbina ogni città al suo paese.",
    "1 | Roma | A | Italia",
    "2 | Lima | B | Perù",
]
ENGLISH_SHEETS = {
    "Instructions": [["Read each item and mark the printed answer only."]],
    "Items": [
        ["number", "question", "type", "options", "answer"],
        ["1", "What number completes the series 2, 4, 8, 16?", "seleccion_multiple", "A) 18; B) 24; C) 32", "C"],
        ["2", "The sun is a star.", "verdadero_falso", "True; False", "True"],
        ["3", "Describe a recent situation in which you felt under pressure.", "desarrollo", "", ""],
        ["4", "I worry about minor things.", "escala_likert", "Never; Sometimes; Often; Always", ""],
    ],
    "Matching": [
        ["5. Match each city with its country."],
        ["1 | Rome | A | Italy"],
        ["2 | Lima | B | Peru"],
        ["Answer: 1-A,2-B"],
    ],
}


def main() -> None:
    settings = get_settings()
    inputs = ROOT / "input"
    outputs = ROOT / "output"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    files = {
        "sample_questionnaire_es.pdf": pdf_bytes(SPANISH_LINES),
        "sample_questionnaire_it.docx": docx_bytes(ITALIAN),
        "sample_questionnaire_en.xlsx": xlsx_bytes(ENGLISH_SHEETS),
        "sample_questionnaire_photo.jpg": _jpeg(SPANISH_LINES[:8]),
    }
    for name, payload in files.items():
        (inputs / name).write_bytes(payload)
    _write("sample_questionnaire_es.json", PdfParser().parse(files["sample_questionnaire_es.pdf"], settings=settings))
    _write("sample_questionnaire_it.json", DocxParser().parse(files["sample_questionnaire_it.docx"], settings=settings))
    _write("sample_questionnaire_en.json", XlsxParser().parse(files["sample_questionnaire_en.xlsx"], settings=settings))
    from app.domain.interfaces.parser import ExtractedDocument, TextLine

    photo_lines = [TextLine(line, 1, heading=index == 0) for index, line in enumerate(SPANISH_LINES[:8])]
    photo_doc = ExtractedDocument(photo_lines, 1)
    _write("sample_questionnaire_photo.json", photo_doc)


def _jpeg(lines: list[str]) -> bytes:
    import io

    from PIL import Image

    data = image_bytes(lines)
    image = Image.open(io.BytesIO(data)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _write(name: str, document) -> None:
    result = run_deterministic(document, threshold=0.7, ocr_used=False, ocr_confidence=None)
    if result.questionnaire is None:
        raise SystemExit(f"No se pudo extraer {name}")
    target = ROOT / "output" / name
    target.write_text(
        json.dumps(result.questionnaire.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
