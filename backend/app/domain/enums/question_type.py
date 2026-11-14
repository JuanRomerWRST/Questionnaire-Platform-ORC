from enum import StrEnum


class QuestionType(StrEnum):
    ESCALA_LIKERT = "escala_likert"
    SELECCION_MULTIPLE = "seleccion_multiple"
    VERDADERO_FALSO = "verdadero_falso"
    DESARROLLO = "desarrollo"
    EMPAREJAMIENTO = "emparejamiento"
