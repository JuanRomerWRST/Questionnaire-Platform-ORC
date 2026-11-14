"""Genera los cuestionarios sintéticos de examples/ a partir del pipeline real."""

import json
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.parsers.docx_parser import DocxParser
from app.infrastructure.parsers.pdf_parser import PdfParser
from app.infrastructure.parsers.xlsx_parser import XlsxParser
from app.services.extraction_service import run_deterministic
from tests.fixtures.builders import SPANISH_LINES, docx_bytes, pdf_bytes, raster_bytes, scanned_pdf, xlsx_bytes

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
LIKERT = [
    "Escala de hábitos de estudio",
    "1. Me resulta fácil empezar las tareas difíciles.",
    "Nunca",
    "A veces",
    "A menudo",
    "Siempre",
    "2. Prefiero estudiar en silencio.",
    "Nunca",
    "A veces",
    "A menudo",
    "Siempre",
]
PAREN = [
    "Repaso de aritmética",
    "1) ¿Cuánto es 3 + 3?",
    "A) 5",
    "B) 6",
    "C) 7",
    "Respuesta correcta: B",
]
CODED = [
    "Capitales",
    "Q1 ¿Cuál es la capital de Perú?",
    "A) Quito",
    "B) Lima",
    "Respuesta correcta: B",
]
NO_KEY = [
    "Sin clave impresa",
    "1. ¿Cuál es el resultado de 2 + 2?",
    "A) 3",
    "B) 4",
    "C) 5",
]
BAD_KEY = [
    "Clave fuera de las opciones",
    "1. ¿De qué color es el cielo despejado?",
    "A) Verde",
    "B) Azul",
    "Respuesta correcta: Z",
]
OPEN_EN = [
    "Open questions",
    "1. Describe a recent situation in which you felt under pressure.",
    "2. Explain how you organize a study afternoon.",
]
VF_IT = [
    "Questionario vero o falso",
    "1. Il sole è una stella. (V/F)",
    "Risposta corretta: V",
    "2. Roma è in Francia. (V/F)",
    "Risposta corretta: F",
]
MATCHING_SHEETS = {
    "Pares": [
        ["1. Relaciona cada ciudad con su país."],
        ["1 | Roma | A | Italia"],
        ["2 | Lima | B | Perú"],
        ["Respuesta correcta: 1-A,2-B"],
    ]
}
LOW_CONFIDENCE = [
    "Cuestionario con texto suelto",
    "1. ¿Cuál es la capital de Francia?",
    "A) Madrid",
    "B) París",
    "Respuesta correcta: B",
    "Este párrafo no es una alternativa y queda suelto después de la clave para que el extractor lo deje sin ítem.",
    "Sigue otro bloque de notas que tampoco tiene número ni opciones y ocupa una parte grande del documento.",
    "Una tercera nota suelta confirma que hay más texto huérfano que el umbral de confianza admite.",
    "4. Describa una tarde de estudio.",
]
SHORT = [
    "Prueba breve",
    "1. ¿Cuánto es 2 + 2?",
    "A) 3",
    "B) 4",
    "Respuesta correcta: B",
]


def main() -> None:
    settings = get_settings()
    inputs = ROOT / "input"
    outputs = ROOT / "output"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    text_files = {
        "sample_questionnaire_es.pdf": pdf_bytes(SPANISH_LINES),
        "sample_questionnaire_it.docx": docx_bytes(ITALIAN),
        "sample_questionnaire_en.xlsx": xlsx_bytes(ENGLISH_SHEETS),
        "es_solo_likert.pdf": pdf_bytes(LIKERT),
        "es_estilo_parentesis.pdf": pdf_bytes(PAREN),
        "es_estilo_q.pdf": pdf_bytes(CODED),
        "es_sin_clave.pdf": pdf_bytes(NO_KEY),
        "es_clave_invalida.pdf": pdf_bytes(BAD_KEY),
        "en_solo_abierta.docx": docx_bytes(OPEN_EN),
        "it_verdadero_falso.docx": docx_bytes(VF_IT),
        "es_emparejamiento.xlsx": xlsx_bytes(MATCHING_SHEETS),
        "es_baja_confianza.pdf": pdf_bytes(LOW_CONFIDENCE),
    }
    visual_files = {
        "es_foto_clara.png": raster_bytes(SPANISH_LINES, "PNG"),
        "es_foto_clara.jpg": raster_bytes(SPANISH_LINES, "JPEG"),
        "es_foto_clara.webp": raster_bytes(SPANISH_LINES, "WEBP"),
        "es_escaneado.pdf": scanned_pdf(SPANISH_LINES),
        "es_foto_corta.png": raster_bytes(SHORT, "PNG"),
        "es_escaneado_corto.pdf": scanned_pdf(SHORT),
    }
    for name, payload in {**text_files, **visual_files}.items():
        (inputs / name).write_bytes(payload)
    parsers = {".pdf": PdfParser, ".docx": DocxParser, ".xlsx": XlsxParser}
    cases = []
    for name in text_files:
        if name == "es_baja_confianza.pdf":
            parsed = PdfParser().parse(text_files[name], settings=settings)
            result = run_deterministic(parsed, threshold=0.7, ocr_used=False, ocr_confidence=None)
            if result.questionnaire is None or not result.confidence.needs_llm:
                raise SystemExit("es_baja_confianza.pdf no quedó por debajo del umbral del modelo")
            cases.append(_case(name, "llm", "Texto con salto de numeración y párrafos sueltos. Debe llamar al modelo sin OCR."))
            continue
        _write(name, parsers[Path(name).suffix]().parse(text_files[name], settings=settings))
        cases.append(_case(name, "deterministic", "Texto nativo. No necesita OCR ni modelo."))
    for name, note in (
        ("es_foto_clara.png", "Foto nítida. OCR, y el modelo queda apagado en esta pasada."),
        ("es_foto_clara.jpg", "La misma foto en JPEG."),
        ("es_foto_clara.webp", "La misma foto en WEBP."),
        ("es_escaneado.pdf", "PDF sin capa de texto. Entra por OCR."),
        ("es_foto_corta.png", "Poco texto. OCR y, si el modelo está activo, también el modelo."),
        ("es_escaneado_corto.pdf", "PDF escaneado corto. OCR y modelo."),
    ):
        mode = "ocr_llm" if "corta" in name or "corto" in name else "ocr"
        cases.append(_case(name, mode, note))
    from app.domain.interfaces.parser import ExtractedDocument, TextLine

    photo_lines = [TextLine(line, 1, heading=index == 0) for index, line in enumerate(SPANISH_LINES[:8])]
    _write("sample_questionnaire_photo.json", ExtractedDocument(photo_lines, 1))
    (inputs / "sample_questionnaire_photo.jpg").write_bytes(raster_bytes(SPANISH_LINES[:8], "JPEG"))
    cases.append(_case("sample_questionnaire_photo.jpg", "reference", "La salida JSON es el texto impreso, no un OCR en vivo."))
    (ROOT / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _case(name: str, mode: str, note: str) -> dict[str, str]:
    return {"file": name, "mode": mode, "note": note}


def _write(name: str, document) -> None:
    result = run_deterministic(document, threshold=0.7, ocr_used=False, ocr_confidence=None)
    if result.questionnaire is None:
        raise SystemExit(f"No se pudo extraer {name}")
    target = ROOT / "output" / Path(name).with_suffix(".json").name
    target.write_text(
        json.dumps(result.questionnaire.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
