export function UploadProgress({ ratio }: { ratio: number | null }) {
  if (ratio === null) return null;
  const percent = Math.round(ratio * 100);
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-[var(--ink-soft)]">
        <span>Subiendo archivo</span>
        <span>{percent}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[var(--paper-2)]" aria-hidden="true">
        <div className="h-full bg-[var(--accent)]" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
