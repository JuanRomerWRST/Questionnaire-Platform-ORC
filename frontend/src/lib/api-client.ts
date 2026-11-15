import { apiUrl } from "@/lib/constants";
import type { AggregatedMetrics, Capabilities, ExtractionResponse } from "@/types/api.types";

export class ApiError extends Error {
  constructor(
    public code: string,
    public status: number,
    message: string,
    public requestId?: string,
    public retryAfter?: number,
  ) {
    super(message);
  }
}

export async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiUrl()}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiError("NETWORK_ERROR", 0, "No se pudo contactar la API.");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      body?.error?.code ?? "HTTP_ERROR",
      response.status,
      body?.error?.message ?? "La solicitud falló.",
      body?.request_id,
    );
  }
  return body as T;
}

export function getCapabilities(): Promise<Capabilities> {
  return getJson<Capabilities>("/documents/capabilities");
}

export async function getMetrics(): Promise<AggregatedMetrics> {
  try {
    return await getJson<AggregatedMetrics>("/metrics");
  } catch (error) {
    if (error instanceof ApiError && error.code === "NETWORK_ERROR" && (await healthReachable())) {
      throw new ApiError(
        "BLOCKED_BY_CLIENT",
        0,
        "Desactiva el adblock. Está bloqueando la consulta de métricas.",
      );
    }
    throw error;
  }
}

async function healthReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${apiUrl()}/health`, { cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}

export function uploadDocument(
  file: File,
  options: { useLlm: boolean; forceOcr: boolean },
  onProgress: (ratio: number | null) => void,
): { promise: Promise<ExtractionResponse>; abort: () => void } {
  const form = new FormData();
  form.append("file", file);
  form.append("use_llm", String(options.useLlm));
  form.append("force_ocr", String(options.forceOcr));
  const xhr = new XMLHttpRequest();
  const promise = new Promise<ExtractionResponse>((resolve, reject) => {
    xhr.open("POST", `${apiUrl()}/documents/extract`);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total);
    };
    xhr.upload.onload = () => onProgress(null);
    xhr.onload = () => {
      const body = safeJson(xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as ExtractionResponse);
        return;
      }
      const retry = Number(xhr.getResponseHeader("Retry-After"));
      reject(
        new ApiError(
          body?.error?.code ?? "HTTP_ERROR",
          xhr.status,
          body?.error?.message ?? "No se pudo procesar el archivo.",
          body?.request_id,
          Number.isFinite(retry) ? retry : undefined,
        ),
      );
    };
    xhr.onerror = () => reject(new ApiError("NETWORK_ERROR", 0, "No se pudo contactar la API."));
    xhr.onabort = () => reject(new ApiError("ABORTED", 0, "La carga fue cancelada."));
    xhr.send(form);
  });
  return { promise, abort: () => xhr.abort() };
}

function safeJson(raw: string): { error?: { code?: string; message?: string }; request_id?: string } | null {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
