"use client";

import { Check, Copy, Download, FileText, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { QuestionCard } from "@/features/questionnaire/components/QuestionCard";
import {
  downloadAnswersPdf,
  downloadQuestionnaire,
} from "@/features/export/services/export.service";
import { useProcessing } from "@/features/processing/hooks/useProcessing";
import { useCapabilities } from "@/hooks/useCapabilities";
import { readPreferences } from "@/lib/preferences";
import { readSourceFile, restoreSourceFile, subscribePreview } from "@/lib/preview-store";
import { readResult, subscribeResult, writeResult } from "@/lib/result-store";
import { cn, formatMs } from "@/lib/utils";
import type { ExtractionResponse } from "@/types/api.types";

type Pane = "items" | "json";

export function ResultBoard() {
  const { capabilities } = useCapabilities();
  const extensions = capabilities.formats.map((format) => format.extension);
  const processing = useProcessing(capabilities.max_upload_size_mb, extensions);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [source, setSource] = useState<File | null>(null);
  const [pane, setPane] = useState<Pane>("items");
  const [selected, setSelected] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const busy = ["validating", "uploading", "processing"].includes(processing.state);

  useEffect(() => {
    // La sesión solo existe en el navegador. Leerla en el render desfasaría el HTML del servidor.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setResult(readResult());
    setSource(readSourceFile());
    void restoreSourceFile().then((file) => {
      if (file) setSource(file);
    });
    const stopResult = subscribeResult(() => setResult(readResult()));
    const stopSource = subscribePreview(() => setSource(readSourceFile()));
    return () => {
      stopResult();
      stopSource();
    };
  }, []);

  useEffect(() => {
    if (!processing.result) return;
    writeResult(processing.result);
  }, [processing.result]);

  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed(Date.now() - started), 200);
    return () => window.clearInterval(timer);
  }, [busy]);

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          Sin resultado en esta sesión
        </h1>
        <p className="mt-3 text-muted-foreground">
          Procesa un documento para ver los ítems y el JSON.
        </p>
        <Button
          type="button"
          className="mt-6"
          onClick={() => {
            // La navegación del cliente se quedaba en resultados. Esta carga abre el formulario.
            // eslint-disable-next-line @next/next/no-location-assign-relative-destination
            window.location.assign("/extract");
          }}
        >
          Nueva extracción
        </Button>
      </div>
    );
  }

  const json = JSON.stringify(result.questionnaire, null, 2);
  const sources = new Map(
    (result.sources ?? []).map((sourceItem) => [sourceItem.numero, sourceItem.pagina]),
  );
  const active = selected ?? result.questionnaire.items[0]?.numero ?? null;
  const fileKind = result.metrics.file_type;

  function location(numero: number): string | undefined {
    const origin = sources.get(numero);
    if (origin && fileKind === "pdf") return `Empieza en la página ${origin} del PDF`;
    if (origin && fileKind === "xlsx") return `Sale de la hoja ${origin}`;
    if (fileKind === "png" || fileKind === "jpeg" || fileKind === "webp") return "Sale de la imagen completa";
    if (result?.metrics.llm_used && !origin) return "El modelo reescribió este ítem. No hay página de origen.";
    return undefined;
  }

  async function copy() {
    setCopyError("");
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopyError("El navegador bloqueó el portapapeles. Selecciona el JSON y usa Ctrl+C.");
      setPane("json");
    }
  }

  async function again() {
    const file = readSourceFile();
    if (!file || busy) return;
    const preferences = readPreferences();
    await processing.process(file, { useLlm: preferences.useLlm, forceOcr: preferences.forceOcr });
  }

  return (
    <div className="min-w-0">
      <p className="text-sm text-muted-foreground">
        {result.status === "partial" ? "Extracción parcial" : "Extracción completa"} · {result.questionnaire.idioma}
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance break-words sm:text-4xl">
        {result.questionnaire.titulo}
      </h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground sm:text-base">
        {result.questionnaire.total_items} ítems · {formatMs(result.metrics.total_processing_ms)} ·{" "}
        {result.metrics.extraction_method}
        {result.metrics.llm_used ? ` · ${result.metrics.llm_model}` : " · sin modelo"}
      </p>

      {result.warnings.length > 0 ? (
        <ul className="mt-4 space-y-2" aria-label="Advertencias">
          {result.warnings.map((warning) => (
            <li
              key={warning.code + warning.message}
              className="rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
            >
              {warning.message}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={copy}>
          {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
          {copied ? "JSON copiado" : "Copiar JSON"}
        </Button>
        <Button type="button" variant="outline" onClick={() => downloadQuestionnaire(result.questionnaire, "cuestionario.json")}>
          <Download size={16} aria-hidden="true" />
          Descargar JSON
        </Button>
        <Button type="button" onClick={() => downloadAnswersPdf(result.questionnaire, "respuestas.pdf")}>
          <FileText size={16} aria-hidden="true" />
          Descargar PDF
        </Button>
        <Button type="button" variant="outline" disabled={!source || busy} onClick={again}>
          <RefreshCw size={16} aria-hidden="true" />
          Extraer de nuevo
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            // La navegación del cliente se quedaba en resultados. Esta carga abre el formulario.
            // eslint-disable-next-line @next/next/no-location-assign-relative-destination
            window.location.assign("/extract");
          }}
        >
          Nueva extracción
        </Button>
      </div>
      {copyError ? <p className="mt-2 text-sm text-destructive">{copyError}</p> : null}
      {!source ? (
        <p className="mt-2 text-sm text-muted-foreground">
          Extraer de nuevo usa el archivo de esta pestaña. Si la recargaste, elige el documento otra vez.
        </p>
      ) : null}

      {busy ? (
        <div className="mt-6 rounded-2xl border border-border bg-card p-5" aria-live="polite">
          <p className="font-medium">
            {processing.state === "validating"
              ? "Comprobando el archivo"
              : processing.state === "uploading"
                ? "Subiendo el archivo"
                : "El servidor está leyendo el documento"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Llevamos {(elapsed / 1000).toFixed(1)} s. Esta cifra es el reloj real, no un avance estimado.
          </p>
        </div>
      ) : null}

      {processing.state === "error" || processing.state === "rate_limited" ? (
        <div role="alert" className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <p>{processing.error}</p>
          {processing.retryAfter ? <p className="mt-1">Puedes reintentar en {processing.retryAfter} segundos.</p> : null}
        </div>
      ) : null}

      <div className="mt-5 flex gap-1 overflow-x-auto xl:hidden" role="tablist" aria-label="Paneles del resultado">
        {(
          [
            ["items", "Ítems"],
            ["json", "JSON"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={pane === value}
            onClick={() => setPane(value)}
            className={cn(
              "min-h-11 shrink-0 cursor-pointer rounded-full px-4 text-sm",
              pane === value ? "bg-accent text-white" : "border border-border bg-card text-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <section className={cn("min-w-0 space-y-3", pane !== "items" && "hidden xl:block")} aria-label="Ítems extraídos">
          <h2 className="text-sm font-semibold">Ítems</h2>
          {result.questionnaire.items.map((item) => (
            <QuestionCard
              key={item.numero}
              item={item}
              location={location(item.numero)}
              selected={item.numero === active}
              onSelect={() => setSelected(item.numero)}
            />
          ))}
        </section>

        <section className={cn("min-w-0", pane !== "json" && "hidden xl:block")} aria-label="JSON del contrato">
          <h2 className="text-sm font-semibold">JSON</h2>
          <p className="mt-1 text-sm text-muted-foreground">Este es el contrato que se copia y se descarga.</p>
          <pre className="mt-3 max-h-[36rem] max-w-full overflow-auto rounded-2xl border border-border bg-card p-4 font-mono text-xs leading-6">
            {json}
          </pre>
          <p className="mt-3 text-sm text-muted-foreground">
            Confianza heurística {result.metrics.confidence_score.toFixed(2)}. No es una probabilidad calibrada.
          </p>
        </section>
      </div>
    </div>
  );
}
