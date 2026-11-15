"use client";

import { Check, Copy, Download, FileText } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { PdfPage } from "@/features/questionnaire/components/PdfPage";
import { QuestionCard } from "@/features/questionnaire/components/QuestionCard";
import {
  downloadAnswersPdf,
  downloadQuestionnaire,
} from "@/features/export/services/export.service";
import {
  readPreview,
  subscribePreview,
  type PreviewFile,
} from "@/lib/preview-store";
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
    // La sesión solo existe en el navegador. Leerla en el render desfasaría el HTML del servidor.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setResult(readResult());
    setPreview(readPreview());
    return subscribeResult(() => setResult(readResult()));
  }, []);
  useEffect(() => subscribePreview(() => setPreview(readPreview())), []);

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl py-16">
        <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          Sin resultado en esta sesión
        </h1>
        <p className="mt-3 text-muted-foreground">
          Procesa un documento para ver el archivo, los ítems y el JSON.
        </p>
        <Button asChild className="mt-6">
          <a href="/extract">Nueva extracción</a>
        </Button>
      </div>
    );
  }

  const json = JSON.stringify(result.questionnaire, null, 2);
  const sources = new Map(
    (result.sources ?? []).map((source) => [source.numero, source.pagina]),
  );
  const active = selected ?? result.questionnaire.items[0]?.numero ?? null;
  const page = active == null ? null : (sources.get(active) ?? null);
  const fileKind = result.metrics.file_type;

  function location(numero: number): string | undefined {
    const origin = sources.get(numero);
    if (origin && fileKind === "pdf")
      return `Empieza en la página ${origin} del PDF`;
    if (origin && fileKind === "xlsx") return `Sale de la hoja ${origin}`;
    if (fileKind === "png" || fileKind === "jpeg" || fileKind === "webp")
      return "Sale de la imagen completa";
    if (result?.metrics.llm_used && !origin)
      return "El modelo reescribió este ítem. No hay página de origen.";
    return undefined;
  }

  async function copy() {
    setCopyError("");
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopyError(
        "El navegador bloqueó el portapapeles. Selecciona el JSON y usa Ctrl+C.",
      );
      setPane("json");
    }
  }

  return (
    <div className="min-w-0">
      <p className="text-sm text-muted-foreground">
        {result.status === "partial"
          ? "Extracción parcial"
          : "Extracción completa"}{" "}
        · {result.questionnaire.idioma}
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance break-words sm:text-4xl">
        {result.questionnaire.titulo}
      </h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground sm:text-base">
        {result.questionnaire.total_items} ítems ·{" "}
        {formatMs(result.metrics.total_processing_ms)} ·{" "}
        {result.metrics.extraction_method}
        {result.metrics.llm_used
          ? ` · ${result.metrics.llm_model}`
          : " · sin modelo"}
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
          {copied ? (
            <Check size={16} aria-hidden="true" />
          ) : (
            <Copy size={16} aria-hidden="true" />
          )}
          {copied ? "JSON copiado" : "Copiar JSON"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            downloadQuestionnaire(result.questionnaire, "cuestionario.json")
          }
        >
          <Download size={16} aria-hidden="true" />
          Descargar JSON
        </Button>
        <Button
          type="button"
          onClick={() =>
            downloadAnswersPdf(result.questionnaire, "respuestas.pdf")
          }
        >
          <FileText size={16} aria-hidden="true" />
          Descargar PDF
        </Button>
      </div>
      {copyError ? (
        <p className="mt-2 text-sm text-destructive">{copyError}</p>
      ) : null}

      <div
        className="mt-5 flex gap-1 overflow-x-auto xl:hidden"
        role="tablist"
        aria-label="Paneles del resultado"
      >
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
              pane === value
                ? "bg-accent text-white"
                : "border border-border bg-card text-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)_minmax(0,0.9fr)]">
        <section className="min-w-0" aria-label="Vista previa del archivo">
          <h2 className="text-sm font-semibold">Archivo</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Cada página marca los ítems que empiezan ahí. Elige un ítem para ir a esa página.
          </p>
          <FilePane
            preview={preview}
            activePage={fileKind === "pdf" || fileKind === "xlsx" ? page : 1}
            pageCount={Math.max(1, result.metrics.pages_or_sheets ?? 1)}
            itemsByPage={itemsByPage(result, fileKind)}
            activeItem={active}
          />
        </section>

        <section
          className={cn(
            "min-w-0 space-y-3",
            pane !== "items" && "hidden xl:block",
          )}
          aria-label="Ítems extraídos"
        >
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

        <section
          className={cn("min-w-0", pane !== "json" && "hidden xl:block")}
          aria-label="JSON del contrato"
        >
          <h2 className="text-sm font-semibold">JSON</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Este es el contrato, sin la vista previa ni las páginas.
          </p>
          <pre className="mt-3 max-h-[36rem] max-w-full overflow-auto rounded-2xl border border-border bg-card p-4 font-mono text-xs leading-6">
            {json}
          </pre>
          <p className="mt-3 text-sm text-muted-foreground">
            Confianza heurística {result.metrics.confidence_score.toFixed(2)}.
            No es una probabilidad calibrada.
          </p>
        </section>
      </div>
    </div>
  );
}

function itemsByPage(result: ExtractionResponse, fileKind: string): Map<number, number[]> {
  const grouped = new Map<number, number[]>();
  const count = Math.max(1, result.metrics.pages_or_sheets ?? 1);
  for (let page = 1; page <= count; page += 1) grouped.set(page, []);
  for (const source of result.sources ?? []) {
    const list = grouped.get(source.pagina) ?? [];
    list.push(source.numero);
    grouped.set(source.pagina, list);
  }
  if ((result.sources ?? []).length === 0 && (fileKind === "png" || fileKind === "jpeg" || fileKind === "webp")) {
    grouped.set(
      1,
      result.questionnaire.items.map((item) => item.numero),
    );
  }
  return grouped;
}

function FilePane({
  preview,
  activePage,
  pageCount,
  itemsByPage: pages,
  activeItem,
}: {
  preview: PreviewFile | null;
  activePage: number | null;
  pageCount: number;
  itemsByPage: Map<number, number[]>;
  activeItem: number | null;
}) {
  const cards = useRef<Record<number, HTMLElement | null>>({});

  useEffect(() => {
    if (activePage == null) return;
    cards.current[activePage]?.scrollIntoView({ block: "nearest" });
  }, [activePage, activeItem]);

  if (!preview) {
    return (
      <p className="mt-3 rounded-2xl border border-border bg-card p-4 text-sm text-muted-foreground">
        La vista previa vive mientras esta pestaña sigue abierta. Vuelve a procesar el archivo para verlo aquí.
      </p>
    );
  }
  if (preview.kind === "other") {
    return (
      <p className="mt-3 rounded-2xl border border-border bg-card p-4 text-sm text-muted-foreground">
        {preview.name} no se puede pintar en el navegador. Los ítems de al lado indican la hoja o el texto del que salieron.
      </p>
    );
  }

  const pageNumbers = preview.kind === "image" ? [1] : Array.from({ length: pageCount }, (_, index) => index + 1);

  return (
    <div className="mt-3 max-h-[36rem] space-y-4 overflow-auto rounded-2xl bg-muted p-3">
      {pageNumbers.map((pageNumber) => {
        const numbers = pages.get(pageNumber) ?? [];
        const current = pageNumber === activePage;
        return (
          <article
            key={pageNumber}
            ref={(node) => {
              cards.current[pageNumber] = node;
            }}
            className={cn(
              "overflow-hidden rounded-xl border bg-white shadow-sm",
              current ? "border-accent ring-2 ring-accent" : "border-border",
            )}
          >
            <div className="flex flex-wrap items-center gap-2 border-b border-border px-3 py-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {preview.kind === "image" ? "Imagen" : `Página ${pageNumber}`}
              </p>
              {numbers.length === 0 ? (
                <span className="text-xs text-muted-foreground">Sin ítems en esta página</span>
              ) : (
                numbers.map((numero) => (
                  <span
                    key={numero}
                    className={cn(
                      "rounded-full px-2 py-1 text-xs font-medium",
                      numero === activeItem ? "bg-accent text-white" : "bg-blue-50 text-blue-900",
                    )}
                  >
                    Ítem {numero}
                  </span>
                ))
              )}
            </div>
            {preview.kind === "pdf" ? (
              <PdfPage url={preview.url} pageNumber={pageNumber} />
            ) : (
              // The image is the source the user uploaded.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview.url} alt={preview.name} className="max-h-80 w-full object-contain" />
            )}
          </article>
        );
      })}
    </div>
  );
}
