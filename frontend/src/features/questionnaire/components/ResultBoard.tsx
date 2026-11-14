"use client";

import { Check, Copy, Download, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { QuestionCard } from "@/features/questionnaire/components/QuestionCard";
import { downloadAnswersPdf, downloadQuestionnaire } from "@/features/export/services/export.service";
import { readPreview, subscribePreview, type PreviewFile } from "@/lib/preview-store";
import { readResult, subscribeResult } from "@/lib/result-store";
import { cn, formatMs } from "@/lib/utils";
import type { ExtractionResponse } from "@/types/api.types";

type Pane = "preview" | "items" | "json";

export function ResultBoard() {
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [preview, setPreview] = useState<PreviewFile | null>(null);
  const [pane, setPane] = useState<Pane>("items");
  const [selected, setSelected] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  useEffect(() => {
    setResult(readResult());
    setPreview(readPreview());
    return subscribeResult(() => setResult(readResult()));
  }, []);
  useEffect(() => subscribePreview(() => setPreview(readPreview())), []);

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">Sin resultado en esta sesión</h1>
        <p className="mt-3 text-muted-foreground">Procesa un documento para ver el archivo, los ítems y el JSON.</p>
        <Button asChild className="mt-6">
          <a href="/extract">Nueva extracción</a>
        </Button>
      </div>
    );
  }

  const json = JSON.stringify(result.questionnaire, null, 2);
  const sources = new Map((result.sources ?? []).map((source) => [source.numero, source.pagina]));
  const active = selected ?? result.questionnaire.items[0]?.numero ?? null;
  const page = active == null ? null : sources.get(active) ?? null;
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

  return (
    <div className="min-w-0">
      <p className="text-sm text-muted-foreground">
        {result.status === "partial" ? "Extracción parcial" : "Extracción completa"} · {result.questionnaire.idioma}
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance break-words sm:text-4xl">{result.questionnaire.titulo}</h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground sm:text-base">
        {result.questionnaire.total_items} ítems · {formatMs(result.metrics.total_processing_ms)} · {result.metrics.extraction_method}
        {result.metrics.llm_used ? ` · ${result.metrics.llm_model}` : " · sin modelo"}
      </p>

      {result.warnings.length > 0 ? (
        <ul className="mt-4 space-y-2" aria-label="Advertencias">
          {result.warnings.map((warning) => (
            <li key={warning.code + warning.message} className="rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
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
      </div>
      {copyError ? <p className="mt-2 text-sm text-destructive">{copyError}</p> : null}

      <div className="mt-5 flex gap-1 overflow-x-auto xl:hidden" role="tablist" aria-label="Paneles del resultado">
        {(
          [
            ["preview", "Archivo"],
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

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)_minmax(0,0.9fr)]">
        <section className={cn("min-w-0", pane !== "preview" && "hidden xl:block")} aria-label="Vista previa del archivo">
          <h2 className="text-sm font-semibold">Archivo</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {page && fileKind === "pdf"
              ? `El visor abre la página ${page}, donde empieza el ítem seleccionado.`
              : "Selecciona un ítem para ver de qué parte del archivo salió."}
          </p>
          <FilePane preview={preview} page={fileKind === "pdf" ? page : null} />
        </section>

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
          <p className="mt-1 text-sm text-muted-foreground">Este es el contrato, sin la vista previa ni las páginas.</p>
          <pre className="mt-3 max-h-[36rem] max-w-full overflow-auto rounded-2xl border border-border bg-card p-4 font-mono text-xs leading-6">{json}</pre>
          <p className="mt-3 text-sm text-muted-foreground">Confianza heurística {result.metrics.confidence_score.toFixed(2)}. No es una probabilidad calibrada.</p>
        </section>
      </div>
    </div>
  );
}

function FilePane({ preview, page }: { preview: PreviewFile | null; page: number | null }) {
  if (!preview) {
    return (
      <p className="mt-3 rounded-2xl border border-border bg-card p-4 text-sm text-muted-foreground">
        La vista previa vive mientras esta pestaña sigue abierta. Vuelve a procesar el archivo para verlo aquí.
      </p>
    );
  }
  if (preview.kind === "pdf") {
    const src = page ? `${preview.url}#page=${page}` : preview.url;
    return (
      <iframe
        key={src}
        title={`Vista previa de ${preview.name}`}
        src={src}
        className="mt-3 h-[28rem] w-full rounded-2xl border border-border bg-white sm:h-[36rem]"
      />
    );
  }
  if (preview.kind === "image") {
    return (
      // The file name is the accessible name of the source the user uploaded.
      // eslint-disable-next-line @next/next/no-img-element
      <img src={preview.url} alt={preview.name} className="mt-3 max-h-[36rem] w-full rounded-2xl border border-border object-contain bg-white" />
    );
  }
  return (
    <p className="mt-3 rounded-2xl border border-border bg-card p-4 text-sm text-muted-foreground">
      {preview.name} no se puede pintar en el navegador. El texto se leyó en el servidor y los ítems están en el panel de al lado.
    </p>
  );
}
