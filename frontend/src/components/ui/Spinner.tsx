export function Spinner({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-[var(--ink-soft)]" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--line)] border-t-[var(--accent)]" />
      {label}
    </span>
  );
}
