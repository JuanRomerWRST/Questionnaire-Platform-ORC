export type ResultView = "structure" | "json";

export type Preferences = {
  useLlm: boolean;
  forceOcr: boolean;
  resultView: ResultView;
};

const KEY = "qi:preferences";
export const DEFAULT_PREFERENCES: Preferences = {
  useLlm: true,
  forceOcr: false,
  resultView: "structure",
};

export function readPreferences(): Preferences {
  if (typeof window === "undefined") return DEFAULT_PREFERENCES;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    return { ...DEFAULT_PREFERENCES, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function writePreferences(next: Preferences) {
  window.localStorage.setItem(KEY, JSON.stringify(next));
  window.dispatchEvent(new Event("qi-preferences"));
}

export function subscribePreferences(onStoreChange: () => void) {
  window.addEventListener("qi-preferences", onStoreChange);
  window.addEventListener("storage", onStoreChange);
  return () => {
    window.removeEventListener("qi-preferences", onStoreChange);
    window.removeEventListener("storage", onStoreChange);
  };
}
