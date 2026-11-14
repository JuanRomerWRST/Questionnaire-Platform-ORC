import re
from dataclasses import dataclass, field

from app.domain.entities.questionnaire import DraftItem, DraftOption
from app.domain.interfaces.parser import TextLine
from app.infrastructure.extraction.regex_patterns import (
    ANSWER_KEY_PAIR,
    ANSWER_MARK,
    INLINE_OPTION,
    LIKERT_VOCAB,
    OPEN_KEYWORDS,
    PATTERNS,
    TRUE_FALSE_MARKER,
    QuestionMatch,
)


@dataclass
class DetectionResult:
    preamble: list[str] = field(default_factory=list)
    items: list[DraftItem] = field(default_factory=list)
    orphan_chars: int = 0
    total_chars: int = 0
    answer_key: dict[int, str] = field(default_factory=dict)
    scale_ctx: list[DraftOption] | None = None


def detect_items(lines: list[TextLine]) -> DetectionResult:
    lines = _expand_rows(lines)
    result = DetectionResult()
    current: DraftItem | None = None
    question_style: str | None = None
    answer_key_mode = False
    matching = False

    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        result.total_chars += len(text)
        if answer_key_mode:
            pair = ANSWER_KEY_PAIR.match(text)
            if pair:
                result.answer_key[int(pair.group(1))] = pair.group(2).upper()
                continue
            answer_key_mode = False
        if _matches(PATTERNS["answer_key_header"], text):
            answer_key_mode = True
            current = _close(current, result)
            continue
        scale = _scale_options(text)
        if scale:
            result.scale_ctx = scale
            continue
        if _matches(PATTERNS["matching_header"], text):
            current = _close(current, result)
            number = result.items[-1].numero + 1 if result.items else 1
            current = DraftItem(numero=number, enunciado=text, matching=True, pagina=line.page)
            matching = True
            continue
        question = _question(text)
        if question and _is_new_question(question, current, question_style):
            current = _close(current, result)
            stem, inline = _split_inline(question.text)
            current = DraftItem(numero=question.number, enunciado=stem, options=inline, pagina=line.page)
            question_style = question.style
            matching = False
            continue
        if question and current is not None:
            current.options.append(DraftOption(texto=question.text, valor=question.number))
            continue
        match_row = _matching_row(text)
        header = _matches(PATTERNS["matching_header"], current.enunciado) if current else False
        if current is not None and match_row and (matching or current.matching or header):
            current.matching = True
            left_n, left_t, right_l, right_t = match_row
            current.options.append(DraftOption(texto=left_t, valor=int(left_n)))
            current.options.append(DraftOption(texto=right_t, valor=right_l.upper()))
            continue
        if current is not None and is_likert_text(text):
            current.options.append(DraftOption(texto=text, valor=None))
            continue
        options = _options(text)
        if current is not None and options:
            current.options.extend(options)
            continue
        answer = _first(PATTERNS["answer_line"], text)
        if current is not None and answer:
            current.raw_answer = answer.group(1).strip()
            continue
        hint = _first(PATTERNS["type_hint"], text)
        if current is not None and hint:
            current.type_hint = hint.group(1).lower()
            continue
        if current is not None and not current.options:
            current.enunciado = f"{current.enunciado} {text}".strip()
            continue
        if current is not None and current.options and _continues_option(text, current):
            current.options[-1].texto = f"{current.options[-1].texto} {text}".strip()
            continue
        if current is None:
            result.preamble.append(text)
        else:
            result.orphan_chars += len(text)
    _close(current, result)
    if not result.items:
        _unnumbered_pass(lines, result)
    _apply_scale(result)
    return result


def _expand_rows(lines: list[TextLine]) -> list[TextLine]:
    expanded: list[TextLine] = []
    for line in lines:
        if "|" not in line.text or _matching_row(line.text):
            expanded.append(line)
            continue
        cells = [cell.strip() for cell in line.text.split("|") if cell.strip()]
        if len(cells) >= 3 and re.fullmatch(r"\d{1,3}", cells[0]):
            expanded.append(TextLine(f"{cells[0]}. {cells[1]}", line.page, line.heading))
            expanded.extend(TextLine(cell, line.page) for cell in cells[2:])
            continue
        expanded.append(line)
    return expanded


def _close(current: DraftItem | None, result: DetectionResult) -> None:
    if current and current.enunciado.strip():
        result.items.append(current)
    return None


def _is_new_question(match: QuestionMatch, current: DraftItem | None, style: str | None) -> bool:
    if current is None:
        return True
    if style is not None and match.style != style:
        return False
    if match.number == 1 and current.numero > 1:
        return False
    return True


def _question(text: str) -> QuestionMatch | None:
    styles = ("keyword", "dotted", "paren", "code", "bare")
    for style, pattern in zip(styles, PATTERNS["question"], strict=True):
        found = pattern.match(text)
        if found:
            return QuestionMatch(int(found.group(1)), found.group(2).strip(), style)
    return None


def _options(text: str) -> list[DraftOption]:
    inline = list(INLINE_OPTION.finditer(text))
    if len(inline) >= 2:
        return _inline_options(text, inline)
    for pattern in PATTERNS["option"][:2]:
        found = pattern.match(text)
        if not found:
            continue
        label, body = found.group(1), found.group(2)
        marked, body = _strip_mark(body)
        valor: int | str = int(label) if label.isdigit() else label.upper()
        return [DraftOption(texto=body, valor=valor, marked=marked)]
    bullet = PATTERNS["option"][2].match(text)
    if bullet:
        marked = bool(re.search(r"☑|☒|\[x\]", text, re.I))
        return [DraftOption(texto=bullet.group(1).strip(), valor=None, marked=marked)]
    return []


def _inline_options(text: str, matches: list[re.Match[str]]) -> list[DraftOption]:
    options: list[DraftOption] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        marked, body = _strip_mark(body)
        if body:
            options.append(DraftOption(texto=body, valor=match.group(1).upper(), marked=marked))
    return options


def _split_inline(text: str) -> tuple[str, list[DraftOption]]:
    matches = list(INLINE_OPTION.finditer(text))
    if len(matches) < 2:
        return text, []
    stem = text[: matches[0].start()].strip() or text
    return stem, _inline_options(text, matches)


def _strip_mark(text: str) -> tuple[bool, str]:
    marked = bool(ANSWER_MARK.search(text))
    cleaned = ANSWER_MARK.sub("", text).strip()
    return marked, cleaned or text.strip()


def _matching_row(text: str) -> tuple[str, str, str, str] | None:
    cells = [cell.strip() for cell in text.split("|")]
    cells = [cell for cell in cells if cell]
    if len(cells) == 4 and cells[0].isdigit() and re.fullmatch(r"[A-Ha-h]", cells[2]):
        return cells[0], cells[1], cells[2], cells[3]
    if len(cells) == 2:
        left = re.match(r"^(\d{1,3})[.)]?\s+(.+)$", cells[0])
        right = re.match(r"^([A-Ha-h])[.)]?\s+(.+)$", cells[1])
        if left and right:
            return left.group(1), left.group(2), right.group(1), right.group(2)
    return None


def _scale_options(text: str) -> list[DraftOption] | None:
    if not (_matches(PATTERNS["scale"], text) or text.count("=") >= 3):
        return None
    anchors = re.findall(r"(\d+)\s*=\s*([^,;]+)", text)
    if len(anchors) < 3:
        return None
    return [DraftOption(texto=label.strip(), valor=int(number)) for number, label in anchors]


def _continues_option(text: str, current: DraftItem) -> bool:
    previous = current.options[-1].texto
    return text[:1].islower() and previous[-1:] not in ".?!"


def _apply_scale(result: DetectionResult) -> None:
    if not result.scale_ctx:
        return
    for item in result.items:
        open_ended = OPEN_KEYWORDS.search(item.enunciado) or TRUE_FALSE_MARKER.search(item.enunciado)
        if not item.options and not item.matching and not open_ended:
            item.options = [
                DraftOption(texto=option.texto, valor=option.valor) for option in result.scale_ctx
            ]


def _unnumbered_pass(lines: list[TextLine], result: DetectionResult) -> None:
    number = 1
    for line in lines:
        text = line.text.strip()
        if text.endswith("?") or text.startswith("¿"):
            result.items.append(DraftItem(numero=number, enunciado=text, pagina=line.page))
            number += 1


def _matches(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(pattern.match(text) for pattern in patterns)


def _first(patterns: list[re.Pattern[str]], text: str) -> re.Match[str] | None:
    for pattern in patterns:
        found = pattern.match(text)
        if found:
            return found
    return None


def is_likert_text(text: str) -> bool:
    return text.casefold().strip() in LIKERT_VOCAB
