import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

const NOTES = [
  { title: "Formatos concretos", body: "PDF, DOCX, XLSX, PNG, JPG y WEBP. Lo demás se rechaza." },
  { title: "La clave, solo si está escrita", body: "El sistema no deduce la respuesta correcta." },
  { title: "Nada se guarda", body: "El archivo vive en memoria durante la solicitud y después se descarta." },
];

export default function OverviewPage() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col justify-center">
      <p className="text-sm text-muted-foreground">Inteligencia documental</p>
      <h1 className="mt-3 max-w-xl text-5xl font-semibold tracking-tight text-balance">El cuestionario, ya estructurado.</h1>
      <p className="mt-5 max-w-lg text-lg leading-8 text-muted-foreground">
        Sube un documento y obtén ítems, alternativas e idioma en un JSON estable. El modelo solo entra si las reglas no bastan.
      </p>
      <div className="mt-8">
        <Button asChild>
          <Link href="/extract">
            Nueva extracción
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </Button>
      </div>
      <ul className="mt-16 grid gap-4 sm:grid-cols-3">
        {NOTES.map((note) => (
          <li key={note.title} className="rounded-2xl border border-border bg-card p-5">
            <h2 className="text-sm font-medium">{note.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{note.body}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
