from pydantic import BaseModel, ConfigDict

from app.domain.enums.document_type import DocumentType


class ExtractOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_llm: bool | None = None
    force_ocr: bool = False


class DocumentInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    size_bytes: int
    filename: str
