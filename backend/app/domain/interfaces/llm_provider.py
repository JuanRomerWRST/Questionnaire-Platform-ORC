from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class LLMRequest:
    text: str
    images: list[bytes] = field(default_factory=list)
    file_type: str = "text"
    draft_payload: dict | None = None


@dataclass
class LLMResult:
    payload: dict
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    async def extract(self, request: LLMRequest) -> LLMResult: ...
