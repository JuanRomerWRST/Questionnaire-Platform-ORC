"use client";

import { FileText, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { FilePreview } from "@/features/document-upload/components/FilePreview";
import { useFileUpload } from "@/features/document-upload/hooks/useFileUpload";
import { useProcessing } from "@/features/processing/hooks/useProcessing";
import { useCapabilities } from "@/hooks/useCapabilities";
import { readPreferences, subscribePreferences, writePreferences, type Preferences } from "@/lib/preferences";
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
  const busy = ["validating", "uploading", "processing"].includes(processing.state);

  async function start() {
    if (!file) return;
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
      <h1 className="mt-2 text-4xl font-semibold tracking-tight">Suelta el cuestionario</h1>
      <p className="mt-3 max-w-xl text-base leading-7 text-muted-foreground">
        PDF, Word, Excel o una fotografía legible. El servidor valida el archivo antes de leerlo.
      </p>

      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          setActive(true);
        }}
        onDragLeave={() => setActive(false)}
        onDrop={(event) => {
          event.preventDefault();
          setActive(false);
          const next = event.dataTransfer.files?.[0];
          if (next) {
            setFile(next);
            processing.setState("selected");
          }
        }}
        className={`mt-8 flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-3xl border bg-card px-6 text-center transition duration-200 ${active ? "border-accent" : "border-border hover:border-accent"}`}
      >
        <span className="grid h-12 w-12 place-items-center rounded-full bg-accent text-white">
          <Upload size={20} aria-hidden="true" />
        </span>
        <span className="mt-4 text-lg font-medium">Arrastra el archivo o elige uno</span>
        <span className="mt-1 text-sm text-muted-foreground">Enter abre el selector cuando esta zona tiene el foco.</span>
        <input
          id={inputId}
          className="sr-only"
          type="file"
          accept={extensions.join(",")}
          onChange={(event) => {
            const next = event.target.files?.[0];
            if (next) {
              setFile(next);
              processing.setState("selected");
            }
          }}
        />
      </label>

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

      {file ? (
        <div className="mt-6 rounded-2xl border border-border bg-card p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium">
            <FileText size={16} aria-hidden="true" />
            Archivo seleccionado
          </div>
          <FilePreview file={file} />
        </div>
      ) : null}

      {processing.state === "uploading" && processing.progress !== null ? (
        <div className="mt-6">
          <div className="mb-2 flex justify-between text-sm text-muted-foreground">
            <span>Subida</span>
            <span>{Math.round(processing.progress * 100)}%</span>
          </div>
          <div
            className="h-1.5 overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(processing.progress * 100)}
            aria-label="Progreso de subida"
          >
            <div className="h-full bg-accent" style={{ width: `${processing.progress * 100}%` }} />
          </div>
        </div>
      ) : null}

      {processing.state === "processing" || processing.state === "validating" ? (
        <div className="mt-6 rounded-2xl border border-border bg-card p-5" aria-live="polite">
          <p className="font-medium">{processing.state === "validating" ? "Comprobando el archivo" : "Extrayendo en el servidor"}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            No hay un porcentaje de esta etapa. La respuesta llega cuando el backend termina.
          </p>
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
