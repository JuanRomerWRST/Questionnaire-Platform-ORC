"use client";

import { useRef, useState } from "react";
import { ApiError, uploadDocument } from "@/lib/api-client";
import type { ProcessState } from "@/features/document-upload/types/upload.types";
import type { ExtractionResponse } from "@/types/api.types";

export function useProcessing(maxMb: number, extensions: string[]) {
  const [state, setState] = useState<ProcessState>("idle");
  const [progress, setProgress] = useState<number | null>(null);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [retryAfter, setRetryAfter] = useState<number | undefined>();
  const abortRef = useRef<(() => void) | null>(null);

  async function process(file: File, options: { useLlm: boolean; forceOcr: boolean }) {
    setResult(null);
    setError("");
    setRetryAfter(undefined);
    setState("validating");
    const extension = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase()}` : "";
    if (!extensions.includes(extension)) {
      setState("error");
      setError("Ese formato no está en la lista soportada.");
      return;
    }
    if (file.size > maxMb * 1024 * 1024) {
      setState("error");
      setError("El archivo supera el tamaño máximo.");
      return;
    }
    setState("uploading");
    setProgress(0);
    const { promise, abort } = uploadDocument(file, options, (ratio) => {
      if (ratio === null) {
        setState("processing");
        setProgress(null);
        return;
      }
      setProgress(ratio);
    });
    abortRef.current = abort;
    try {
      const response = await promise;
      setResult(response);
      setState(response.status === "partial" ? "partial" : "success");
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === "ABORTED") return;
      if (caught instanceof ApiError && caught.status === 429) {
        setState("rate_limited");
        setRetryAfter(caught.retryAfter);
        setError(caught.message);
        return;
      }
      setState("error");
      setError(caught instanceof ApiError ? caught.message : "Error inesperado.");
    }
  }

  return { state, setState, progress, result, error, retryAfter, process, abort: () => abortRef.current?.() };
}
