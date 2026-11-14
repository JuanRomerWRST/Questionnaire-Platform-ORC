import re
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    StrictInt,
    field_validator,
    model_validator,
)

from app.domain.enums.question_type import QuestionType

_LANGUAGE = re.compile(r"^([a-z]{2}|und)$")
UNTITLED = "Cuestionario sin título"


class AnswerOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valor: StrictInt | str
    texto: str

    @field_validator("valor")
    @classmethod
    def clean_valor(cls, value: int | str) -> int | str:
        if isinstance(value, bool):
            raise ValueError("valor no puede ser booleano")
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("valor vacío")
            return cleaned
        return value

    @field_validator("texto")
    @classmethod
    def clean_texto(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("texto vacío")
        return cleaned


class QuestionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: PositiveInt
    enunciado: str
    tipo: QuestionType
    alternativas: list[AnswerOption] = Field(default_factory=list)
    respuesta_correcta: StrictInt | str | None = None

    @field_validator("alternativas", mode="before")
    @classmethod
    def none_to_list(cls, value: object) -> object:
        if value is None:
            return []
        return value

    @field_validator("enunciado")
    @classmethod
    def clean_enunciado(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("enunciado vacío")
        return cleaned

    @field_validator("respuesta_correcta", mode="before")
    @classmethod
    def clean_answer(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def check_shape(self) -> Self:
        count = len(self.alternativas)
        tipo = self.tipo
        if tipo == QuestionType.DESARROLLO and count != 0:
            raise ValueError("desarrollo no admite alternativas")
        if tipo == QuestionType.VERDADERO_FALSO and count != 2:
            raise ValueError("verdadero_falso requiere exactamente 2 alternativas")
        if tipo in {QuestionType.SELECCION_MULTIPLE, QuestionType.ESCALA_LIKERT} and count < 2:
            raise ValueError("se requieren al menos 2 alternativas")
        if tipo == QuestionType.EMPAREJAMIENTO:
            integers = sum(isinstance(option.valor, int) for option in self.alternativas)
            letters = sum(isinstance(option.valor, str) for option in self.alternativas)
            if count < 2 or integers < 1 or letters < 1:
                raise ValueError("emparejamiento requiere una columna numérica y una alfabética")
        if self.respuesta_correcta is not None:
            _assert_answer_belongs(self)
        return self


def _assert_answer_belongs(item: QuestionItem) -> None:
    known = {str(option.valor).casefold() for option in item.alternativas}
    raw = str(item.respuesta_correcta).strip()
    if item.tipo == QuestionType.EMPAREJAMIENTO and "-" in raw:
        pairs = [pair.strip() for pair in raw.split(",") if pair.strip()]
        if not pairs:
            raise ValueError("respuesta de emparejamiento vacía")
        for pair in pairs:
            left, separator, right = pair.partition("-")
            left_ok = left.strip().casefold() in known
            right_ok = right.strip().casefold() in known
            if not separator or not left_ok or not right_ok:
                raise ValueError("respuesta de emparejamiento no coincide con las alternativas")
        return
    if raw.casefold() not in known:
        raise ValueError("respuesta_correcta no pertenece a las alternativas")


class Questionnaire(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str = UNTITLED
    idioma: str
    total_items: int | None = None
    items: list[QuestionItem]

    @field_validator("idioma")
    @classmethod
    def clean_language(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _LANGUAGE.fullmatch(cleaned):
            raise ValueError("idioma inválido")
        return cleaned

    @field_validator("titulo")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        return cleaned or UNTITLED

    @model_validator(mode="after")
    def check_totals(self) -> Self:
        if self.total_items is None:
            self.total_items = len(self.items)
        if self.total_items != len(self.items):
            raise ValueError("total_items no coincide con la cantidad de ítems")
        numbers = [item.numero for item in self.items]
        if len(numbers) != len(set(numbers)):
            raise ValueError("numero duplicado")
        if numbers != sorted(numbers):
            raise ValueError("la numeración debe ser estrictamente ascendente")
        return self
