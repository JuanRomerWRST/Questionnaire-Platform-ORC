from dataclasses import dataclass, field

from app.domain.enums.question_type import QuestionType


@dataclass
class DraftOption:
    texto: str
    valor: int | str | None = None
    marked: bool = False


@dataclass
class DraftItem:
    numero: int
    enunciado: str
    options: list[DraftOption] = field(default_factory=list)
    raw_answer: str | None = None
    type_hint: str | None = None
    matching: bool = False
    tipo: QuestionType | None = None
    conflicts: list[str] = field(default_factory=list)


@dataclass
class DraftQuestionnaire:
    titulo: str
    idioma: str
    items: list[DraftItem]
    warnings: list[tuple[str, str]] = field(default_factory=list)
