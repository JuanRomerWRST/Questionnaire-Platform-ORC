import { formatBytes } from "@/lib/utils";

export function FilePreview({ file }: { file: File }) {
  const extension = file.name.includes(".") ? file.name.split(".").pop() : "sin extensión";
  return (
    <dl className="grid grid-cols-3 gap-3 text-sm">
      <div>
        <dt className="text-[var(--ink-soft)]">Nombre</dt>
        <dd className="truncate font-medium">{file.name}</dd>
      </div>
      <div>
        <dt className="text-[var(--ink-soft)]">Extensión</dt>
        <dd className="font-medium uppercase">{extension}</dd>
      </div>
      <div>
        <dt className="text-[var(--ink-soft)]">Tamaño</dt>
        <dd className="font-medium">{formatBytes(file.size)}</dd>
      </div>
    </dl>
  );
}
