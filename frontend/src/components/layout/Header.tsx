export function Header() {
  return (
    <header className="border-b border-[var(--line)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
            <rect width="28" height="28" rx="8" fill="#0f6e6b" />
            <path d="M8 9h12M8 14h8M8 19h10" stroke="white" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          <div>
            <p className="text-sm font-semibold tracking-tight">Questionnaire Intelligence</p>
            <p className="text-xs text-[var(--ink-soft)]">Extracción estructurada</p>
          </div>
        </div>
      </div>
    </header>
  );
}
