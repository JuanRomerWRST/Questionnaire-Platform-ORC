import { formatBytes } from "@/lib/utils";

export function SupportedFormats({ extensions, maxMb }: { extensions: string[]; maxMb: number }) {
  return (
    <p className="text-sm text-[var(--ink-soft)]">
      Formatos: {extensions.join(", ")}. Tamaño máximo {formatBytes(maxMb * 1024 * 1024)}.
    </p>
  );
}
