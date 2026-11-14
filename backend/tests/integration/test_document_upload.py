import asyncio
import io

import pytest

from app.core.exceptions import AppError
from app.infrastructure.llm.base import LLMQuotaError
from tests.fixtures.builders import SPANISH_LINES, docx_bytes, pdf_bytes, xlsx_bytes


def _upload(client, name: str, data: bytes, content_type: str):
    return client.post(
        "/api/v1/documents/extract",
        files={"file": (name, io.BytesIO(data), content_type)},
    )


@pytest.mark.anyio
async def test_pdf_docx_and_xlsx_upload(client):
    pdf = await _upload(client, "sample.pdf", pdf_bytes(SPANISH_LINES), "application/pdf")
    assert pdf.status_code == 200
    body = pdf.json()
    assert body["metrics"]["llm_used"] is False
    assert body["questionnaire"]["total_items"] == len(body["questionnaire"]["items"])
    assert {item["tipo"] for item in body["questionnaire"]["items"]} >= {
        "seleccion_multiple",
        "verdadero_falso",
        "desarrollo",
        "escala_likert",
        "emparejamiento",
    }
    assert body["questionnaire"]["items"][0]["respuesta_correcta"] == "B"

    docx = await _upload(
        client,
        "sample.docx",
        docx_bytes(
            ["Questionario di esempio", "1. Quale numero completa la serie?"],
            [["A) 18", "B) 24", "C) 32"]],
        ),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert docx.status_code == 200

    workbook = xlsx_bytes(
        {
            "Items": [
                ["number", "question", "type", "options", "answer"],
                ["1", "What is two plus two?", "seleccion_multiple", "A) 3; B) 4", "B"],
                ["2", "Describe a recent calm day.", "desarrollo", "", ""],
            ]
        }
    )
    sheet = await _upload(
        client,
        "sample.xlsx",
        workbook,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    assert sheet.status_code == 200
    assert sheet.json()["questionnaire"]["idioma"] == "en"


@pytest.mark.anyio
async def test_prose_without_questions_is_controlled(client):
    data = pdf_bytes(["Este texto solo describe el paisaje y no formula ninguna pregunta concreta."])
    response = await _upload(client, "prose.pdf", data, "application/pdf")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_QUESTIONS_DETECTED"


@pytest.mark.anyio
async def test_unsupported_and_oversized(client, monkeypatch):
    response = await _upload(client, "virus.exe", b"MZ\x90\x00extra", "application/octet-stream")
    assert response.status_code == 415
    monkeypatch.setattr(client._transport.app.state.settings, "max_upload_size_mb", 0)
    response = await _upload(client, "big.pdf", pdf_bytes(["1. ¿Hola?"]), "application/pdf")
    assert response.status_code == 413


@pytest.mark.anyio
async def test_concurrent_uploads_do_not_mix(client):
    async def one(title: str, question: str):
        data = pdf_bytes([title, f"1. {question}", "A) Sí", "B) No"])
        response = await _upload(client, "item.pdf", data, "application/pdf")
        return response.json()

    results = await asyncio.gather(
        *[one(f"Cuestionario {index}", f"Pregunta exclusiva número {index} sobre estudio") for index in range(6)]
    )
    titles = [result["questionnaire"]["titulo"] for result in results]
    assert len(set(titles)) == 6
    assert len({result["request_id"] for result in results}) == 6


@pytest.mark.anyio
async def test_llm_quota_keeps_deterministic_result(client):
    class QuotaProvider:
        async def extract(self, request):
            raise LLMQuotaError("sin saldo")

    settings = client._transport.app.state.settings
    settings.openai_enabled = True
    settings.openai_api_key = "test-key"
    settings.openai_model = "gpt-6-luna"
    settings.confidence_threshold = 1.1
    client._transport.app.state.llm_provider = QuotaProvider()
    response = await _upload(client, "sample.pdf", pdf_bytes(SPANISH_LINES), "application/pdf")
    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert any(warning["code"] == "LLM_QUOTA_EXCEEDED" for warning in response.json()["warnings"])


def test_app_error_shape():
    error = AppError(422, "NO_QUESTIONS_DETECTED", "No se detectaron preguntas en el documento.")
    assert error.status_code == 422
