import type { QuestionItem } from "@/features/questionnaire/types/questionnaire.types";
import { AnswerOptions } from "@/features/questionnaire/components/AnswerOptions";

export function QuestionCard({ item }: { item: QuestionItem }) {
  return (
    <article className="rounded-2xl border border-border bg-card p-5">
      <div className="mb-3 flex items-baseline justify-between gap-4">
        <h3 className="text-sm font-medium text-muted-foreground">Ítem {item.numero}</h3>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{item.tipo.replaceAll("_", " ")}</p>
      </div>
      <p className="text-base leading-7">{item.enunciado}</p>
      <div className="mt-4">
        <AnswerOptions options={item.alternativas} correct={item.respuesta_correcta} />
      </div>
    </article>
  );
}
