from app.domain.entities.questionnaire import DraftItem


def resolve_answers(items: list[DraftItem], answer_key: dict[int, str]) -> list[tuple[str, str]]:
    warnings: list[tuple[str, str]] = []
    for item in items:
        explicit = item.raw_answer
        if explicit is None:
            marked = [option for option in item.options if option.marked and option.valor is not None]
            if len(marked) == 1:
                explicit = str(marked[0].valor)
            elif item.numero in answer_key:
                explicit = answer_key[item.numero]
        if explicit is None:
            continue
        if not _belongs(item, explicit):
            item.raw_answer = None
            warnings.append(
                (
                    "ANSWER_NOT_IN_OPTIONS",
                    f"La respuesta indicada del ítem {item.numero} no coincide con una alternativa.",
                )
            )
            continue
        item.raw_answer = explicit.strip()
    return warnings


def _belongs(item: DraftItem, answer: str) -> bool:
    if not item.options:
        return False
    known = {str(option.valor).casefold() for option in item.options if option.valor is not None}
    raw = answer.strip()
    if "-" in raw and "," in raw or (item.matching and "-" in raw):
        pairs = [part.strip() for part in raw.split(",") if part.strip()]
        return all(_pair_ok(pair, known) for pair in pairs)
    return raw.casefold() in known


def _pair_ok(pair: str, known: set[str]) -> bool:
    left, separator, right = pair.partition("-")
    return bool(separator and left.strip().casefold() in known and right.strip().casefold() in known)
