import { QuestionCard } from "@/features/questionnaire/components/QuestionCard";
import { countByType } from "@/features/questionnaire/services/questionnaire.service";
import type { Questionnaire } from "@/features/questionnaire/types/questionnaire.types";

export function QuestionnairePreview({ questionnaire }: { questionnaire: Questionnaire }) {
  const counts = countByType(questionnaire);
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{questionnaire.titulo}</h2>
        <p className="text-sm text-[var(--ink-soft)]">
          Idioma {questionnaire.idioma}. {questionnaire.total_items} ítems.
        </p>
        <p className="mt-1 text-xs text-[var(--ink-soft)]">
          {Object.entries(counts)
            .filter(([, count]) => count > 0)
            .map(([type, count]) => `${type}: ${count}`)
            .join(" · ")}
        </p>
      </div>
      <div className="space-y-3">
        {questionnaire.items.map((item) => (
          <QuestionCard key={item.numero} item={item} />
        ))}
      </div>
    </div>
  );
}
