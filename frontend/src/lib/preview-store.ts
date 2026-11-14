export type PreviewKind = "pdf" | "image" | "other";

export type PreviewFile = {
  name: string;
  kind: PreviewKind;
  url: string;
};

let current: PreviewFile | null = null;
const listeners = new Set<() => void>();

export function rememberPreview(file: File) {
  if (current) URL.revokeObjectURL(current.url);
  const extension = file.name.includes(".") ? file.name.split(".").pop()?.toLowerCase() : "";
  const kind: PreviewKind =
    extension === "pdf" || file.type === "application/pdf"
      ? "pdf"
      : extension && ["png", "jpg", "jpeg", "webp"].includes(extension)
        ? "image"
        : "other";
  current = { name: file.name, kind, url: URL.createObjectURL(file) };
  listeners.forEach((listener) => listener());
}

export function readPreview(): PreviewFile | null {
  return current;
}

export function subscribePreview(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
