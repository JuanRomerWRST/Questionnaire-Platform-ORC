from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from app.schemas.metrics import ProcessingMetrics
from app.schemas.questionnaire import Questionnaire


class WarningItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ItemSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: PositiveInt
    pagina: PositiveInt


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal["success", "partial"]
    questionnaire: Questionnaire
    metrics: ProcessingMetrics
    warnings: list[WarningItem] = Field(default_factory=list)
    sources: list[ItemSource] = Field(default_factory=list)


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    error: ErrorBody


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    version: str


class FormatCapability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extension: str
    mime_types: list[str]


class CapabilitiesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formats: list[FormatCapability]
    max_upload_size_mb: int
    max_pdf_pages: int
    ocr_available: bool
    llm_available: bool
