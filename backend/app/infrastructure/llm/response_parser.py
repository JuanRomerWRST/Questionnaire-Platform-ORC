from pydantic import BaseModel, Field, ValidationError

from app.domain.enums.question_type import QuestionType
from app.schemas.questionnaire import Questionnaire


class LLMOption(BaseModel):
    valor: str
    texto: str


class LLMItem(BaseModel):
    numero: int
    enunciado: str
    tipo: str
    alternativas: list[LLMOption] = Field(default_factory=list)
    respuesta_correcta: str | None = None
    incierto: bool = False


class LLMQuestionnaire(BaseModel):
    titulo: str = "Cuestionario sin título"
    idioma: str = "und"
    items: list[LLMItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def parse_llm_payload(payload: dict) -> tuple[Questionnaire | None, list[tuple[str, str]]]:
    try:
        parsed = LLMQuestionnaire.model_validate(payload)
    except ValidationError:
        return None, [("LLM_FAILED", "La respuesta del modelo no cumple el esquema.")]
    warnings = [("LLM_UNCERTAIN_CONTENT", message) for message in parsed.warnings if message]
    items = []
    for item in parsed.items:
        if item.tipo not in {tipo.value for tipo in QuestionType}:
            warnings.append(("LLM_FAILED", f"Se descartó el ítem {item.numero} por un tipo no permitido."))
            continue
        if item.incierto:
            warnings.append(("LLM_UNCERTAIN_CONTENT", f"El ítem {item.numero} tiene texto incierto."))
        options = []
        for option in item.alternativas:
            valor: int | str = int(option.valor) if option.valor.isdigit() else option.valor
            options.append({"valor": valor, "texto": option.texto})
        answer = item.respuesta_correcta
        known = {str(option["valor"]).casefold() for option in options}
        if answer and answer.casefold() not in known and "-" not in answer:
            answer = None
            warnings.append(("ANSWER_NOT_IN_OPTIONS", f"Se anuló la respuesta del ítem {item.numero}."))
        items.append(
            {
                "numero": item.numero,
                "enunciado": item.enunciado,
                "tipo": item.tipo,
                "alternativas": options,
                "respuesta_correcta": answer,
            }
        )
    if not items and parsed.items:
        return None, warnings
    try:
        questionnaire = Questionnaire.model_validate(
            {"titulo": parsed.titulo, "idioma": parsed.idioma, "items": items}
        )
    except ValidationError:
        return None, warnings + [("LLM_FAILED", "No se pudo normalizar la respuesta del modelo.")]
    return questionnaire, warnings
