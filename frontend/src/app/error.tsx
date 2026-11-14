"use client";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto max-w-xl px-5 py-16">
      <h1 className="text-xl font-semibold">No se pudo mostrar esta pantalla</h1>
      <button
        type="button"
        className="mt-4 min-h-11 rounded-full bg-[var(--accent)] px-5 text-sm font-semibold text-white"
        onClick={reset}
      >
        Reintentar
      </button>
    </div>
  );
}
