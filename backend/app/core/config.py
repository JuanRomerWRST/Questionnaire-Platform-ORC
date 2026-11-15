from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "questionnaire-intelligence"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    cors_origins: str = "http://localhost:3000"
    max_upload_size_mb: int = 15
    max_pdf_pages: int = 100
    request_timeout_seconds: int = 90

    max_xlsx_sheets: int = 20
    max_xlsx_rows_per_sheet: int = 5000
    max_image_pixels: int = 40_000_000
    max_zip_uncompressed_mb: int = 100
    max_zip_entries: int = 1000
    max_zip_ratio: int = 100
    max_ocr_pages: int = 10
    ocr_languages: str = "spa+eng+ita"
    max_concurrent_ocr: int = 2
    max_concurrent_requests: int = 8
    confidence_threshold: float = 0.70
    llm_max_images: int = 4
    llm_max_input_chars: int = 40_000
    llm_image_max_side: int = 2048

    openai_enabled: bool = False
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = ""
    openai_timeout_seconds: int = 45
    openai_max_retries: int = 2
    openai_max_concurrent_requests: int = 3

    llm_provider: str = "openai"
    llm_mock_latency_ms: int = 50

    ocr_enabled: bool = True
    tesseract_cmd: str = ""
    metrics_token: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        twins: list[str] = []
        for origin in origins:
            if "://localhost" in origin:
                twins.append(origin.replace("://localhost", "://127.0.0.1", 1))
            elif "://127.0.0.1" in origin:
                twins.append(origin.replace("://127.0.0.1", "://localhost", 1))
        return list(dict.fromkeys([*origins, *twins]))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def llm_configured(self) -> bool:
        return bool(
            self.openai_enabled and self.openai_api_key.strip() and self.openai_model.strip()
        )

    @property
    def use_mock_llm(self) -> bool:
        return self.llm_provider.strip().lower() == "mock"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.use_mock_llm and settings.app_env.lower() == "production":
        raise RuntimeError("LLM_PROVIDER=mock no está permitido cuando APP_ENV=production")
    return settings
