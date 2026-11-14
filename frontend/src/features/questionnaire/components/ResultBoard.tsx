"use client";

import * as Tabs from "@radix-ui/react-tabs";
import { Check, Copy, Download } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { QuestionCard } from "@/features/questionnaire/components/QuestionCard";
import { countByType } from "@/features/questionnaire/services/questionnaire.service";
import { downloadQuestionnaire } from "@/features/export/services/export.service";
import { readPreferences, subscribePreferences, writePreferences, type Preferences, type ResultView } from "@/lib/preferences";
import { readResult, subscribeResult } from "@/lib/result-store";
import type { ExtractionResponse } from "@/types/api.types";
import { formatMs } from "@/lib/utils";
import type { ProcessingMetrics } from "@/types/api.types";

const STAGES: Array<[keyof ProcessingMetrics, string]> = [
  ["validation_ms", "Validación"],
  ["parsing_ms", "Lectura"],
  ["ocr_ms", "OCR"],
  ["deterministic_extraction_ms", "Reglas"],
  ["llm_ms", "Modelo"],
  ["validation_output_ms", "Contrato"],
];

export function ResultBoard() {
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [preferences, setPreferences] = useState<Preferences>(readPreferences);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setResult(readResult());
    setPreferences(readPreferences());
    return subscribeResult(() => setResult(readResult()));
  }, []);

  useEffect(() => subscribePreferences(() => setPreferences(readPreferences())), []);

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <h1 className="text-4xl font-semibold tracking-tight">Sin resultado en esta sesión</h1>
        <p className="mt-3 text-muted-foreground">Procesa un documento para ver la estructura y el JSON.</p>
        <Button asChild className="mt-6">
          <a href="/extract">Nueva extracción</a>
        </Button>
      </div>
    );
  }

  const counts = countByType(result.questionnaire);
  const json = JSON.stringify(result.questionnaire, null, 2);

  async function copy() {
    await navigator.clipboard.writeText(json);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="mx-auto max-w-4xl">
      <p className="text-sm text-muted-foreground">
        {result.status === "partial" ? "Extracción parcial" : "Extracción completa"} · {result.questionnaire.idioma}
      </p>
      <h1 className="mt-2 text-4xl font-semibold tracking-tight">{result.questionnaire.titulo}</h1>
      <p className="mt-3 text-muted-foreground">
        {result.questionnaire.total_items} ítems · {formatMs(result.metrics.total_processing_ms)} · {result.metrics.extraction_method}
        {result.metrics.llm_used ? ` · ${result.metrics.llm_model}` : " · sin modelo"}
      </p>

      {result.warnings.length > 0 ? (
        <ul className="mt-6 space-y-2" aria-label="Advertencias">
          {result.warnings.map((warning) => (
            <li key={warning.code + warning.message} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
              {warning.message}
            </li>
          ))}
        </ul>
      ) : null}

      <Tabs.Root
        className="mt-8"
        value={preferences.resultView}
        onValueChange={(value) => writePreferences({ ...preferences, resultView: value as ResultView })}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Tabs.List className="flex rounded-full border border-border bg-card p-1" aria-label="Modo de lectura">
            <Tabs.Trigger value="structure" className="min-h-11 cursor-pointer rounded-full px-4 text-sm data-[state=active]:bg-accent data-[state=active]:text-white">
              Estructura
            </Tabs.Trigger>
            <Tabs.Trigger value="json" className="min-h-11 cursor-pointer rounded-full px-4 text-sm data-[state=active]:bg-accent data-[state=active]:text-white">
              JSON
            </Tabs.Trigger>
          </Tabs.List>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={copy}>
              {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
              {copied ? "Copiado" : "Copiar JSON"}
            </Button>
            <Button type="button" variant="outline" onClick={() => downloadQuestionnaire(result.questionnaire, "cuestionario.json")}>
              <Download size={16} aria-hidden="true" />
              Descargar
            </Button>
          </div>
        </div>

        <Tabs.Content value="structure" className="mt-6 space-y-3 focus-visible:outline-none">
          <p className="text-sm text-muted-foreground">
            {Object.entries(counts)
              .filter(([, count]) => count > 0)
              .map(([type, count]) => `${type.replaceAll("_", " ")} ${count}`)
              .join(" · ")}
          </p>
          {result.questionnaire.items.map((item) => (
            <QuestionCard key={item.numero} item={item} />
          ))}
        </Tabs.Content>
        <Tabs.Content value="json" className="mt-6 focus-visible:outline-none">
          <pre className="max-h-[32rem] overflow-auto rounded-2xl border border-border bg-card p-5 font-mono text-xs leading-6">{json}</pre>
        </Tabs.Content>
      </Tabs.Root>

      <section className="mt-10" aria-label="Tiempos de esta solicitud">
        <h2 className="text-sm font-medium text-muted-foreground">Tiempos medidos</h2>
        <ul className="mt-3 grid gap-3 sm:grid-cols-3">
          {STAGES.map(([key, label]) => (
            <li key={key} className="rounded-2xl border border-border bg-card px-4 py-3">
              <span className="block text-xs text-muted-foreground">{label}</span>
              <span className="mt-1 block text-lg font-medium">{formatMs(Number(result.metrics[key] ?? 0))}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-muted-foreground">
          Confianza heurística {result.metrics.confidence_score.toFixed(2)}. No es una probabilidad calibrada.
        </p>
      </section>
    </div>
  );
}
