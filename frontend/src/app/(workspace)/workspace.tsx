"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FilePreview } from "@/features/document-upload/components/FilePreview";
import { FileUploader } from "@/features/document-upload/components/FileUploader";
import { SupportedFormats } from "@/features/document-upload/components/SupportedFormats";
import { UploadProgress } from "@/features/document-upload/components/UploadProgress";
import { useFileUpload } from "@/features/document-upload/hooks/useFileUpload";
import { DownloadJsonButton } from "@/features/export/components/DownloadJsonButton";
import { ProcessingError } from "@/features/processing/components/ProcessingError";
import { ProcessingMetrics } from "@/features/processing/components/ProcessingMetrics";
import { ProcessingStatus } from "@/features/processing/components/ProcessingStatus";
import { useProcessing } from "@/features/processing/hooks/useProcessing";
import { JsonViewer } from "@/features/questionnaire/components/JsonViewer";
import { QuestionnairePreview } from "@/features/questionnaire/components/QuestionnairePreview";
import { useCapabilities } from "@/hooks/useCapabilities";

export function Workspace() {
  const { capabilities, offline } = useCapabilities();
  const extensions = capabilities.formats.map((format) => format.extension);
  const { file, setFile } = useFileUpload();
  const processing = useProcessing(capabilities.max_upload_size_mb, extensions);
  const [useLlm, setUseLlm] = useState(true);
  const [forceOcr, setForceOcr] = useState(false);
  const busy = ["validating", "uploading", "processing"].includes(processing.state);

  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-5 py-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <div className="space-y-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Del documento al JSON</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--ink-soft)]">
            Sube un cuestionario en PDF, DOCX, XLSX o imagen. Las reglas locales estructuran el contenido y el modelo solo interviene si hace falta.
          </p>
        </div>
        <Card className="space-y-4">
          <FileUploader
            extensions={extensions}
            onFile={(next) => {
              setFile(next);
              processing.setState("selected");
            }}
          />
          <SupportedFormats extensions={extensions} maxMb={capabilities.max_upload_size_mb} />
          {offline ? <p className="text-sm text-[#6f2c28]">La API no responde. Revisa que el backend esté en marcha.</p> : null}
          <p className="text-xs text-[var(--ink-soft)]">
            OCR {capabilities.ocr_available ? "disponible" : "no disponible"}. Modelo {capabilities.llm_available ? "configurado" : "apagado"}.
          </p>
          {file ? <FilePreview file={file} /> : null}
          <UploadProgress ratio={processing.progress} />
          <ProcessingStatus state={file ? processing.state : "idle"} />
          <div className="flex flex-wrap gap-4 text-sm">
            <label className="inline-flex min-h-11 items-center gap-2">
              <input type="checkbox" checked={useLlm} onChange={(event) => setUseLlm(event.target.checked)} />
              Permitir modelo si la confianza es baja
            </label>
            <label className="inline-flex min-h-11 items-center gap-2">
              <input type="checkbox" checked={forceOcr} onChange={(event) => setForceOcr(event.target.checked)} />
              Forzar OCR
            </label>
          </div>
          <div className="flex gap-3">
            <Button
              type="button"
              disabled={!file || busy}
              onClick={() => file && processing.process(file, { useLlm, forceOcr })}
            >
              Procesar
            </Button>
            {busy ? (
              <Button type="button" variant="ghost" onClick={processing.abort}>
                Cancelar
              </Button>
            ) : null}
          </div>
          {processing.state === "error" || processing.state === "rate_limited" ? (
            <ProcessingError
              message={processing.error}
              retryAfter={processing.retryAfter}
              onRetry={() => file && processing.process(file, { useLlm, forceOcr })}
            />
          ) : null}
        </Card>
      </div>
      <Card>
        {processing.result ? (
          <div className="space-y-6">
            <QuestionnairePreview questionnaire={processing.result.questionnaire} />
            {processing.result.warnings.length > 0 ? (
              <ul className="space-y-1 text-sm text-[#6d4710]">
                {processing.result.warnings.map((warning) => (
                  <li key={warning.code + warning.message}>{warning.message}</li>
                ))}
              </ul>
            ) : null}
            <ProcessingMetrics metrics={processing.result.metrics} />
            <JsonViewer value={processing.result.questionnaire} />
            <DownloadJsonButton questionnaire={processing.result.questionnaire} />
          </div>
        ) : (
          <p className="text-sm text-[var(--ink-soft)]">El resultado, las métricas y el JSON aparecerán aquí.</p>
        )}
      </Card>
    </div>
  );
}
