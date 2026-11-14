"use client";

import { FileText, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useFileUpload } from "@/features/document-upload/hooks/useFileUpload";
import { useProcessing } from "@/features/processing/hooks/useProcessing";
import { useCapabilities } from "@/hooks/useCapabilities";
import { readPreferences, subscribePreferences, writePreferences, type Preferences } from "@/lib/preferences";
import { rememberPreview } from "@/lib/preview-store";
import { writeResult } from "@/lib/result-store";
import { formatBytes } from "@/lib/utils";

export function ExtractionDesk() {
  const router = useRouter();
  const inputId = useId();
  const { capabilities, offline } = useCapabilities();
  const extensions = capabilities.formats.map((format) => format.extension);
  const [preferences, setPreferences] = useState<Preferences>(readPreferences);
  useEffect(() => subscribePreferences(() => setPreferences(readPreferences())), []);
  const { file, setFile } = useFileUpload();
  const processing = useProcessing(capabilities.max_upload_size_mb, extensions);
  const [active, setActive] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    function keepInPage(event: DragEvent) {
      event.preventDefault();
    }
    window.addEventListener("dragover", keepInPage);
    window.addEventListener("drop", keepInPage);
    return () => {
      window.removeEventListener("dragover", keepInPage);
      window.removeEventListener("drop", keepInPage);
    };
  }, []);

  function choose(next: File) {
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return next.type.startsWith("image/") ? URL.createObjectURL(next) : null;
    });
    setFile(next);
    processing.setState("selected");
  }
  const busy = ["validating", "uploading", "processing"].includes(processing.state);

  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed(Date.now() - started), 200);
    return () => window.clearInterval(timer);
  }, [busy]);

  async function start() {
    if (!file) return;
    rememberPreview(file);
    await processing.process(file, { useLlm: preferences.useLlm, forceOcr: preferences.forceOcr });
  }

  useEffect(() => {
    if (!processing.result) return;
    writeResult(processing.result);
    router.push("/results");
  }, [processing.result, router]);

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-sm text-muted-foreground">Nueva extracción</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance sm:text-4xl">Suelta el cuestionario</h1>
      <p className="mt-3 max-w-xl text-base leading-7 text-muted-foreground">
        PDF, Word, Excel o una fotografía legible. El servidor valida el archivo antes de leerlo.
      </p>

      <div
        data-dropzone
        onDragEnter={(event) => {
          event.preventDefault();
          setActive(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = "copy";
          setActive(true);
        }}
        onDragLeave={(event) => {
          if (event.currentTarget.contains(event.relatedTarget as Node | null)) return;
          setActive(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setActive(false);
          const next = event.dataTransfer.files?.[0];
          if (next) choose(next);
        }}
        className={`mt-8 flex min-h-64 flex-col items-center justify-center rounded-3xl border bg-card px-6 py-8 text-center transition duration-200 ${active ? "border-accent bg-blue-50" : "border-border"}`}
      >
        {file ? (
          <div className="w-full max-w-md text-left">
            {previewUrl ? (
              // The preview is the file the user just dropped.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl} alt="" className="mb-4 max-h-48 w-full rounded-xl border border-border object-contain bg-white" />
            ) : (
              <span className="mb-4 grid h-12 w-12 place-items-center rounded-full bg-accent text-white">
                <FileText size={20} aria-hidden="true" />
              </span>
            )}
            <p className="text-base font-medium break-all">{file.name}</p>
            <p className="mt-1 text-sm text-muted-foreground">{formatBytes(file.size)} listos para procesar</p>
          </div>
        ) : (
          <>
            <span className="grid h-12 w-12 place-items-center rounded-full bg-accent text-white">
              <Upload size={20} aria-hidden="true" />
            </span>
            <span className="mt-4 text-lg font-medium">Arrastra el archivo aquí</span>
            <span className="mt-1 text-sm text-muted-foreground">o elige uno desde el equipo</span>
          </>
        )}
        <label htmlFor={inputId} className="mt-4 inline-flex min-h-11 cursor-pointer items-center rounded-full border border-border bg-white px-4 text-sm font-medium">
          Elegir archivo
          <input
            id={inputId}
            className="sr-only"
            type="file"
            accept={extensions.join(",")}
            onChange={(event) => {
              const next = event.target.files?.[0];
              if (next) choose(next);
            }}
          />
        </label>
      </div>

      <ul className="mt-4 flex flex-wrap gap-2" aria-label="Formatos soportados">
        {extensions.map((extension) => (
          <li key={extension} className="rounded-full border border-border bg-card px-3 py-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {extension.replace(".", "")}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-muted-foreground">
        Hasta {formatBytes(capabilities.max_upload_size_mb * 1024 * 1024)}. OCR {capabilities.ocr_available ? "disponible" : "no instalado en este proceso"}. Modelo {capabilities.llm_available ? "configurado" : "apagado"}.
      </p>
      {offline ? <p className="mt-3 text-sm text-destructive">La API no responde.</p> : null}

      {busy ? (
        <div className="mt-6 rounded-2xl border border-border bg-card p-5" aria-live="polite">
          <p className="font-medium">
            {processing.state === "validating"
              ? "Comprobando el archivo"
              : processing.state === "uploading"
                ? "Subiendo el archivo"
                : "El servidor está leyendo el documento"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">Llevamos {(elapsed / 1000).toFixed(1)} s. Esta cifra es el reloj real, no un avance estimado.</p>
          {processing.state === "uploading" && processing.progress !== null ? (
            <div
              className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(processing.progress * 100)}
              aria-label="Progreso de subida"
            >
              <div className="h-full bg-accent" style={{ width: `${processing.progress * 100}%` }} />
            </div>
          ) : (
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted" role="status" aria-label="Extracción en curso">
              <div className="h-full w-1/3 animate-[slide_1.2s_ease-in-out_infinite] bg-accent" />
            </div>
          )}
        </div>
      ) : null}

      {processing.state === "error" || processing.state === "rate_limited" ? (
        <div role="alert" className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <p>{processing.error}</p>
          {processing.retryAfter ? <p className="mt-1">Puedes reintentar en {processing.retryAfter} segundos.</p> : null}
        </div>
      ) : null}

      <div className="mt-6 flex flex-wrap gap-3">
        <Button type="button" disabled={!file || busy} onClick={start}>
          Procesar
        </Button>
        {busy ? (
          <Button type="button" variant="outline" onClick={processing.abort}>
            Cancelar
          </Button>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          onClick={() => writePreferences({ ...preferences, useLlm: !preferences.useLlm })}
        >
          Modelo {preferences.useLlm ? "permitido" : "desactivado"}
        </Button>
      </div>
    </div>
  );
}
