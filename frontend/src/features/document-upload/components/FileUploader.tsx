"use client";

import { useId, useState } from "react";

export function FileUploader({
  extensions,
  onFile,
}: {
  extensions: string[];
  onFile: (file: File) => void;
}) {
  const inputId = useId();
  const [active, setActive] = useState(false);
  return (
    <label
      htmlFor={inputId}
      onDragOver={(event) => {
        event.preventDefault();
        setActive(true);
      }}
      onDragLeave={() => setActive(false)}
      onDrop={(event) => {
        event.preventDefault();
        setActive(false);
        const file = event.dataTransfer.files?.[0];
        if (file) onFile(file);
      }}
      className={`flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed px-6 py-8 text-center ${active ? "border-[var(--accent)] bg-[#eef6f5]" : "border-[var(--line)] bg-white"}`}
    >
      <span className="text-base font-semibold">Suelta el cuestionario o elige un archivo</span>
      <span className="mt-2 text-sm text-[var(--ink-soft)]">También puedes pulsar Enter cuando el área tenga el foco.</span>
      <input
        id={inputId}
        className="sr-only"
        type="file"
        accept={extensions.join(",")}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
        }}
      />
    </label>
  );
}
