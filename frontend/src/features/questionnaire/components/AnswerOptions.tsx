import type { AnswerOption } from "@/features/questionnaire/types/questionnaire.types";

export function AnswerOptions({
  options,
  correct,
}: {
  options: AnswerOption[];
  correct: number | string | null;
}) {
  if (options.length === 0) return <p className="text-sm text-muted-foreground">Pregunta abierta. El documento no indica una respuesta.</p>;
  return (
    <ul className="space-y-2">
      {options.map((option) => {
        const marked = correct !== null && String(option.valor).toLowerCase() === String(correct).toLowerCase();
        return (
          <li
            key={`${option.valor}-${option.texto}`}
            className={
              marked
                ? "flex gap-3 rounded-xl border border-blue-700 bg-blue-50 px-3 py-2 text-sm leading-6 text-blue-950"
                : "flex gap-3 rounded-xl px-3 py-2 text-sm leading-6"
            }
          >
            <span className="w-8 shrink-0 font-semibold">{String(option.valor)}</span>
            <span className="min-w-0 break-words">
              {option.texto}
              {marked ? <span className="mt-1 block font-semibold">Respuesta indicada en el documento</span> : null}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
