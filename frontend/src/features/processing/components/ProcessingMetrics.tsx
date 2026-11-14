import { Badge } from "@/components/ui/Badge";
import { formatMs } from "@/lib/utils";
import type { ProcessingMetrics as Metrics } from "@/types/api.types";

const STAGES: Array<[keyof Metrics, string]> = [
  ["validation_ms", "Validación"],
  ["parsing_ms", "Lectura"],
  ["ocr_ms", "OCR"],
  ["deterministic_extraction_ms", "Reglas"],
  ["llm_ms", "Modelo"],
  ["validation_output_ms", "Contrato"],
];

export function ProcessingMetrics({ metrics }: { metrics: Metrics }) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge tone={metrics.status === "success" ? "good" : "warn"}>{metrics.status}</Badge>
        <Badge>{metrics.extraction_method}</Badge>
        <Badge>{metrics.llm_used ? `LLM ${metrics.llm_model ?? ""}` : "Sin LLM"}</Badge>
        <Badge>{`Confianza ${metrics.confidence_score.toFixed(2)}`}</Badge>
      </div>
      <p className="text-sm">Duración total {formatMs(metrics.total_processing_ms)}. Ítems {metrics.items_detected}.</p>
      <ul className="grid gap-2 sm:grid-cols-3">
        {STAGES.map(([key, label]) => (
          <li key={key} className="rounded-2xl bg-[var(--paper)] px-3 py-2 text-sm">
            <span className="block text-[var(--ink-soft)]">{label}</span>
            {formatMs(Number(metrics[key] ?? 0))}
          </li>
        ))}
      </ul>
      {metrics.input_tokens != null ? (
        <p className="text-xs text-[var(--ink-soft)]">
          Tokens de entrada {metrics.input_tokens}, salida {metrics.output_tokens ?? 0}.
        </p>
      ) : null}
    </div>
  );
}
