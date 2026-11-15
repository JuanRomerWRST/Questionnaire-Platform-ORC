const configuredApiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export function apiUrl(): string {
  if (typeof window === "undefined") return configuredApiUrl;
  return configuredApiUrl.replace("://localhost", "://127.0.0.1");
}

export const FALLBACK_FORMATS = [".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".webp"];

export const FALLBACK_MAX_MB = 15;
