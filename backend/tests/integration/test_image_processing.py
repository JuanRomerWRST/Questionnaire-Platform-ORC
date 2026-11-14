import io

import pytest

from app.infrastructure.ocr.base import OcrResult
from tests.fixtures.builders import SPANISH_LINES, image_bytes


class FakeOCR:
    def __init__(self, text: str, confidence: float = 90) -> None:
        self.text = text
        self.confidence = confidence

    def available(self) -> bool:
        return True

    def recognize(self, image, langs: str) -> OcrResult:
        return OcrResult(self.text, self.confidence)


@pytest.mark.anyio
async def test_image_uses_ocr_text(client):
    client._transport.app.state.ocr_engine = FakeOCR("\n".join(SPANISH_LINES))
    response = await client.post(
        "/api/v1/documents/extract",
        files={"file": ("photo.png", io.BytesIO(image_bytes(SPANISH_LINES)), "image/png")},
        data={"use_llm": "false"},
    )
    assert response.status_code == 200
    assert response.json()["metrics"]["extraction_method"] == "ocr"
    assert response.json()["metrics"]["llm_used"] is False


@pytest.mark.anyio
async def test_low_ocr_without_llm_stays_controlled(client):
    client._transport.app.state.ocr_engine = FakeOCR("???", 10)
    response = await client.post(
        "/api/v1/documents/extract",
        files={"file": ("blur.png", io.BytesIO(image_bytes(["..."])), "image/png")},
        data={"use_llm": "false"},
    )
    assert response.status_code in {200, 422}
    if response.status_code == 422:
        assert response.json()["error"]["code"] in {"NO_TEXT_EXTRACTED", "NO_QUESTIONS_DETECTED"}
        return
    codes = {item["code"] for item in response.json()["warnings"]}
    assert "LLM_DISABLED_BY_REQUEST" in codes or "LOW_CONFIDENCE" in codes or "OCR_LOW_QUALITY" in codes
