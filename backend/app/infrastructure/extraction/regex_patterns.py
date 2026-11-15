import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionMatch:
    number: int
    text: str
    style: str


def compile_patterns() -> dict[str, list[re.Pattern[str]]]:
    flags = re.IGNORECASE
    return {
        "question": [
            re.compile(
                r"^\s*(?:pregunta|question|domanda|ítem|item)\s*(\d{1,3})\s*[.):\-]\s+(.+)$",
                flags,
            ),
            re.compile(r"^\s*(\d{1,3})\s*\.\s+(.+)$"),
            re.compile(r"^\s*(\d{1,3})\s*\)\s+(.+)$"),
            re.compile(r"^\s*[QPD](\d{1,3})[.):]?\s+(.+)$", flags),
            re.compile(r"^\s*0*(\d{1,3})\s+(?=[¿¡\"“A-ZÁÉÍÓÚÀÈÌÒÙ])(.+)$"),
        ],
        "option": [
            re.compile(r"^\s*[(\[]?([A-Ha-h])[)\].:]\s*(.+)$"),
            re.compile(r"^\s*[(\[]?(\d{1,2})[)\]]\s*(.+)$"),
            re.compile(r"^\s*(?:☐|☑|☒|□|■|○|●|◯|\[\s?\]|\[x\]|\[X\]|-)\s+(.+)$"),
        ],
        "answer_line": [
            re.compile(
                r"^(?:respuesta(?:\s+correcta)?|clave|answer|correct answer|"
                r"risposta(?:\s+corretta)?|soluzione)\s*[:=]\s*(.+)$",
                flags,
            )
        ],
        "answer_key_header": [
            re.compile(
                r"^(?:respuestas|clave de respuestas|answer key|answers|soluzioni|risposte)\s*:?$",
                flags,
            )
        ],
        "type_hint": [
            re.compile(
                r"^(?:tipo|type)\s*:\s*(escala_likert|seleccion_multiple|"
                r"verdadero_falso|desarrollo|emparejamiento)\s*$",
                flags,
            )
        ],
        "matching_header": [
            re.compile(
                r"^(?:relaciona|relacione|une|empareja|match|matching|abbina|collega|"
                r"columna a|column a|colonna a)\b",
                flags,
            )
        ],
        "scale": [
            re.compile(r"^(?:escala|scale|scala)\b.*:", flags),
        ],
    }


PATTERNS = compile_patterns()

ANSWER_KEY_PAIR = re.compile(
    r"^\s*(\d{1,3})\s*[.):\-→]\s*([A-Ha-h]|\d{1,2}|V|F|T)\s*$",
    re.IGNORECASE,
)
INLINE_OPTION = re.compile(r"(?<!\S)([A-H])[).]\s+")
TRUE_FALSE_MARKER = re.compile(r"\(\s*[VTF]\s*/\s*[VTF]\s*\)", re.IGNORECASE)
ANSWER_MARK = re.compile(
    r"^(?:\*|✓|✔|☑|☒|\[x\]|\(x\))\s*|(\s*\((?:correcta|correct|corretta)\))$",
    re.IGNORECASE,
)
OPEN_KEYWORDS = re.compile(
    r"\b(describa|describe|explique|explain|justifique|justify|comente|por qué|why|"
    r"descriva|spieghi|perché|escriba|scriva|write)\b",
    re.IGNORECASE,
)
BLANK_LINE = re.compile(r"_{4,}|\.{6,}")

LIKERT_VOCAB = {
    "nunca",
    "casi nunca",
    "a veces",
    "algunas veces",
    "a menudo",
    "frecuentemente",
    "casi siempre",
    "siempre",
    "totalmente en desacuerdo",
    "en desacuerdo",
    "ni de acuerdo ni en desacuerdo",
    "neutral",
    "de acuerdo",
    "totalmente de acuerdo",
    "never",
    "rarely",
    "sometimes",
    "often",
    "always",
    "strongly disagree",
    "disagree",
    "agree",
    "strongly agree",
    "mai",
    "raramente",
    "a volte",
    "qualche volta",
    "spesso",
    "sempre",
    "per niente d'accordo",
    "in disaccordo",
    "né d'accordo né in disaccordo",
    "d'accordo",
    "molto d'accordo",
}

VF_VOCAB = {
    "verdadero",
    "falso",
    "true",
    "false",
    "vero",
    "falso",
    "v",
    "f",
    "t",
}
