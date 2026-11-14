import { Spinner } from "@/components/ui/Spinner";
import type { ProcessState } from "@/features/document-upload/types/upload.types";

const LABELS: Record<ProcessState, string> = {
  idle: "Esperando un archivo",
  selected: "Archivo listo para procesar",
  validating: "Validando el archivo",
  uploading: "Enviando el archivo",
  processing: "Procesando el documento",
  success: "Extracción completada",
  partial: "Extracción parcial, revisa las advertencias",
  error: "No se pudo completar la extracción",
  rate_limited: "Demasiadas solicitudes en curso",
};

export function ProcessingStatus({ state }: { state: ProcessState }) {
  const busy = state === "validating" || state === "uploading" || state === "processing";
  return (
    <div aria-live="polite" className="flex items-center justify-between gap-3">
      <p className="text-sm font-medium">{LABELS[state]}</p>
      {busy ? <Spinner label={state === "processing" ? "Tiempo indeterminado" : "En curso"} /> : null}
    </div>
  );
}
