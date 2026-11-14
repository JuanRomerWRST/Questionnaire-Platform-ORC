import type { ExtractionResponse } from "@/types/api.types";

const KEY = "qi:last-result";

export function readResult(): ExtractionResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as ExtractionResponse) : null;
  } catch {
    return null;
  }
}

export function writeResult(result: ExtractionResponse) {
  window.sessionStorage.setItem(KEY, JSON.stringify(result));
  window.dispatchEvent(new Event("qi-result"));
}

export function subscribeResult(onStoreChange: () => void) {
  window.addEventListener("qi-result", onStoreChange);
  return () => window.removeEventListener("qi-result", onStoreChange);
}
