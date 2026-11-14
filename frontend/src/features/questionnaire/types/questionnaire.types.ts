export type QuestionType =
  | "escala_likert"
  | "seleccion_multiple"
  | "verdadero_falso"
  | "desarrollo"
  | "emparejamiento";

export interface AnswerOption {
  valor: number | string;
  texto: string;
}

export interface QuestionItem {
  numero: number;
  enunciado: string;
  tipo: QuestionType;
  alternativas: AnswerOption[];
  respuesta_correcta: number | string | null;
}

export interface Questionnaire {
  titulo: string;
  idioma: string;
  total_items: number;
  items: QuestionItem[];
}
