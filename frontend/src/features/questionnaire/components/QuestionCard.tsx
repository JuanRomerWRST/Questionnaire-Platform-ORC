import { Badge } from "@/components/ui/Badge";
import { AnswerOptions } from "@/features/questionnaire/components/AnswerOptions";
import type { QuestionItem } from "@/features/questionnaire/types/questionnaire.types";

export function QuestionCard({ item }: { item: QuestionItem }) {
  return (
    <article className="rounded-2xl border border-[var(--line)] bg-white p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">Ítem {item.numero}</h3>
        <Badge>{item.tipo}</Badge>
      </div>
      <p className="mb-3 text-sm leading-6">{item.enunciado}</p>
      <AnswerOptions options={item.alternativas} correct={item.respuesta_correcta} />
    </article>
  );
}
