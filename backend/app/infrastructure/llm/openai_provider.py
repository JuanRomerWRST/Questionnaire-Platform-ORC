import base64
import io
import logging

from PIL import Image, ImageOps

from app.core.config import Settings
from app.domain.interfaces.llm_provider import LLMRequest, LLMResult
from app.infrastructure.llm.base import (
    LLMAuthError,
    LLMError,
    LLMInvalidResponseError,
    LLMQuotaError,
    LLMTimeoutError,
    LLMUnavailableError,
    with_retries,
)
from app.infrastructure.llm.prompts.image_extraction import IMAGE_HINT
from app.infrastructure.llm.prompts.questionnaire_extraction import SYSTEM_PROMPT, build_text_input
from app.infrastructure.llm.prompts.text_fidelity import TEXT_FIDELITY_RULES
from app.infrastructure.llm.response_parser import LLMQuestionnaire

logger = logging.getLogger(__name__)


class OpenAIProvider:
    def __init__(self, settings: Settings, client=None) -> None:
        self._settings = settings
        self._client = client

    async def extract(self, request: LLMRequest) -> LLMResult:
        if not self._settings.llm_configured:
            raise LLMInvalidResponseError("OpenAI no está configurado.")

        async def attempt() -> LLMResult:
            client = self._client_or_create()
            try:
                response = await client.responses.parse(
                    model=self._settings.openai_model,
                    instructions=f"{TEXT_FIDELITY_RULES}\n{SYSTEM_PROMPT}",
                    input=self._input(request),
                    text_format=LLMQuestionnaire,
                    reasoning={"effort": "low"},
                    store=False,
                    max_output_tokens=4000,
                )
            except Exception as exc:
                mapped = _map_error(exc)
                if mapped is exc:
                    raise
                raise mapped from exc
            parsed = getattr(response, "output_parsed", None)
            if parsed is None:
                raise LLMInvalidResponseError("El modelo no devolvió un JSON utilizable.")
            usage = getattr(response, "usage", None)
            logger.info(
                "llm call completed",
                extra={"request_id": ""},
            )
            return LLMResult(
                payload=parsed.model_dump(),
                model=self._settings.openai_model,
                input_tokens=_usage_value(usage, "input_tokens", "prompt_tokens"),
                output_tokens=_usage_value(usage, "output_tokens", "completion_tokens"),
            )

        return await with_retries(attempt, self._settings.openai_max_retries)

    def _client_or_create(self):
        if self._client is not None:
            return self._client
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=self._settings.openai_api_key,
            timeout=self._settings.openai_timeout_seconds,
            max_retries=0,
        )
        return self._client

    def _input(self, request: LLMRequest) -> list[dict]:
        text = build_text_input(request.text[: self._settings.llm_max_input_chars])
        content: list[dict] = [{"type": "input_text", "text": text}]
        if request.images:
            content.insert(
                0,
                {
                    "type": "input_text",
                    "text": (
                        f"{IMAGE_HINT}\n"
                        "El bloque <document> es el texto OCR. Las imágenes adjuntas son el original. "
                        "Compara ambas fuentes y recupera solo los caracteres que la imagen respalda."
                    ),
                },
            )
            for image in request.images[: self._settings.llm_max_images]:
                content.append(
                    {
                        "type": "input_image",
                        "image_url": _jpeg_data_url(image, self._settings.llm_image_max_side),
                    }
                )
        return [{"role": "user", "content": content}]


class MockLLMProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def extract(self, request: LLMRequest) -> LLMResult:
        import asyncio

        await asyncio.sleep(self._settings.llm_mock_latency_ms / 1000)
        payload = request.draft_payload or {
            "titulo": "Cuestionario sin título",
            "idioma": "und",
            "items": [],
        }
        return LLMResult(payload=payload, model="mock", input_tokens=1, output_tokens=1)


def build_llm_provider(settings: Settings):
    if settings.use_mock_llm:
        return MockLLMProvider(settings)
    return OpenAIProvider(settings)


def _jpeg_data_url(data: bytes, max_side: int) -> str:
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    image.thumbnail((max_side, max_side))
    if image.mode != "RGB":
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _usage_value(usage, *names: str) -> int | None:
    if usage is None:
        return None
    for name in names:
        value = getattr(usage, name, None)
        if value is not None:
            return int(value)
    return None


def _map_error(exc: Exception) -> Exception:
    if isinstance(exc, LLMError):
        return exc
    name = exc.__class__.__name__
    message = str(exc)
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return LLMAuthError("La API de OpenAI rechazó la autenticación.")
    if name == "RateLimitError":
        code = getattr(exc, "code", "") or ""
        if code in {"insufficient_quota", "credit_balance_exhausted"} or "insufficient_quota" in message:
            return LLMQuotaError("La cuenta de OpenAI no tiene saldo disponible.")
        return LLMError(
            "OpenAI aplicó un límite de tasa.",
            transient=False,
            retry_after=_retry_after(exc),
        )
    if name in {"APITimeoutError", "APIConnectionError"}:
        return LLMTimeoutError()
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and status >= 500:
        return LLMUnavailableError()
    if name == "BadRequestError":
        return LLMInvalidResponseError("OpenAI rechazó la solicitud.")
    return exc


def _retry_after(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    if response is None:
        return None
    raw = response.headers.get("retry-after")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None
