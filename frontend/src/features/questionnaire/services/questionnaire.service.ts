import type { Questionnaire, QuestionType } from "@/features/questionnaire/types/questionnaire.types";

export function countByType(questionnaire: Questionnaire): Record<QuestionType, number> {
  const counts: Record<QuestionType, number> = {
    escala_likert: 0,
    seleccion_multiple: 0,
    verdadero_falso: 0,
    desarrollo: 0,
    emparejamiento: 0,
  };
  for (const item of questionnaire.items) counts[item.tipo] += 1;
  return counts;
}
