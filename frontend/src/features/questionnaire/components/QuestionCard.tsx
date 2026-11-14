import type { QuestionItem } from "@/features/questionnaire/types/questionnaire.types";
import { AnswerOptions } from "@/features/questionnaire/components/AnswerOptions";
import { cn } from "@/lib/utils";

export function QuestionCard({
  item,
  location,
  selected,
  onSelect,
}: {
  item: QuestionItem;
  location?: string;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <article className={cn("rounded-2xl border bg-card p-4 sm:p-5", selected ? "border-accent ring-2 ring-accent" : "border-border")}>
      <button type="button" onClick={onSelect} className="w-full cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold">Ítem {item.numero}</h3>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{item.tipo.replaceAll("_", " ")}</p>
        </div>
        <p className="text-base leading-7 break-words">{item.enunciado}</p>
        {location ? <p className="mt-2 text-sm font-medium text-blue-800">{location}</p> : null}
      </button>
      <div className="mt-4">
        <AnswerOptions options={item.alternativas} correct={item.respuesta_correcta} />
      </div>
    </article>
  );
}
