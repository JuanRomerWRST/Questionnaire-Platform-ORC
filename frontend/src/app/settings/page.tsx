"use client";

import * as Switch from "@radix-ui/react-switch";
import { useEffect, useState } from "react";
import { readPreferences, subscribePreferences, writePreferences, type Preferences } from "@/lib/preferences";

export default function SettingsPage() {
  const [preferences, setPreferences] = useState<Preferences>(readPreferences);
  useEffect(() => subscribePreferences(() => setPreferences(readPreferences())), []);

  function update(partial: Partial<typeof preferences>) {
    writePreferences({ ...preferences, ...partial });
  }

  return (
    <div className="mx-auto max-w-2xl">
      <p className="text-sm text-muted-foreground">Preferencias de esta máquina</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Ajustes</h1>
      <p className="mt-4 text-muted-foreground">
        Aquí no se guardan claves. La API de OpenAI vive solo en el servidor.
      </p>
      <ul className="mt-8 divide-y divide-border rounded-2xl border border-border bg-card">
        <Setting
          label="Permitir el modelo"
          hint="Solo se llama si la extracción local no es confiable."
          checked={preferences.useLlm}
          onCheckedChange={(useLlm) => update({ useLlm })}
        />
        <Setting
          label="Forzar OCR"
          hint="Aplica a PDF e imágenes. En Office se ignora con una advertencia."
          checked={preferences.forceOcr}
          onCheckedChange={(forceOcr) => update({ forceOcr })}
        />
      </ul>
    </div>
  );
}

function Setting({
  label,
  hint,
  checked,
  onCheckedChange,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
}) {
  const id = label.replaceAll(" ", "-").toLowerCase();
  return (
    <li className="flex flex-col items-start gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
      <div>
        <label htmlFor={id} className="text-sm font-medium">
          {label}
        </label>
        <p className="mt-1 text-sm text-muted-foreground">{hint}</p>
      </div>
      <Switch.Root
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        className="h-7 w-12 shrink-0 cursor-pointer rounded-full bg-muted data-[state=checked]:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <Switch.Thumb className="block h-5 w-5 translate-x-1 rounded-full bg-white transition duration-200 data-[state=checked]:translate-x-6" />
      </Switch.Root>
    </li>
  );
}
