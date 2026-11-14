import type { AnswerOption } from "@/features/questionnaire/types/questionnaire.types";

export function AnswerOptions({
  options,
  correct,
}: {
  options: AnswerOption[];
  correct: number | string | null;
}) {
  if (options.length === 0) return <p className="text-sm text-muted-foreground">Pregunta abierta.</p>;
  return (
    <ul className="space-y-2">
      {options.map((option) => {
        const marked = correct !== null && String(option.valor).toLowerCase() === String(correct).toLowerCase();
        return (
          <li key={`${option.valor}-${option.texto}`} className="flex gap-3 text-sm leading-6">
            <span className="w-8 shrink-0 font-medium text-muted-foreground">{String(option.valor)}</span>
            <span>
              {option.texto}
              {marked ? <span className="ml-2 font-medium text-accent">Indicada en el documento</span> : null}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
