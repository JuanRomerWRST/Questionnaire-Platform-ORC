"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ApiError, getMetrics } from "@/lib/api-client";
import { formatMs } from "@/lib/utils";
import type { AggregatedMetrics } from "@/types/api.types";

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<AggregatedMetrics | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setMetrics(await getMetrics());
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "No se pudieron leer las métricas.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const empty = metrics != null && metrics.requests_total === 0;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">Laboratorio</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance sm:text-4xl">Rendimiento de este proceso</h1>
        </div>
        <Button type="button" variant="outline" onClick={load} disabled={loading}>
          <RefreshCw size={16} aria-hidden="true" />
          Actualizar
        </Button>
      </div>
      <p className="mt-4 max-w-2xl text-muted-foreground">
        Estas cifras salen de la memoria del backend que está respondiendo ahora. Se borran al reiniciar y no representan un clúster.
      </p>
      {error ? (
        <p role="alert" className="mt-6 text-sm text-destructive">
          {error}
        </p>
      ) : null}
      {loading && !metrics ? <p className="mt-8 text-sm text-muted-foreground">Leyendo métricas…</p> : null}
      {empty ? <p className="mt-8 text-sm text-muted-foreground">Todavía no hay solicitudes en este proceso.</p> : null}
      {metrics && !empty ? (
        <>
          <ul className="mt-8 grid gap-3 sm:grid-cols-3">
            <Stat label="Solicitudes" value={String(metrics.requests_total)} hint={`${metrics.requests_success} correctas · ${metrics.requests_failed} fallidas · ${metrics.requests_partial} parciales`} />
            <Stat label="En curso" value={String(metrics.in_flight)} hint={`Máximo observado ${metrics.max_concurrency}`} />
            <Stat label="Throughput" value={`${metrics.throughput_rps.toFixed(2)} /s`} hint={`Media ${formatMs(metrics.latency_avg_ms)}`} />
            <Stat label="p50" value={formatMs(metrics.latency_p50_ms)} />
            <Stat label="p95" value={formatMs(metrics.latency_p95_ms)} hint={metrics.latency_p95_ms == null ? "Hacen falta más muestras" : undefined} />
            <Stat label="p99" value={formatMs(metrics.latency_p99_ms)} hint={metrics.latency_p99_ms == null ? "Hacen falta más muestras" : undefined} />
          </ul>
          <h2 className="mt-10 text-sm font-medium text-muted-foreground">Promedio por etapa</h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-3">
            {Object.entries(metrics.avg_stage_ms).map(([key, value]) => (
              <li key={key} className="rounded-2xl border border-border bg-card px-4 py-3">
                <span className="block text-xs text-muted-foreground">{key.replaceAll("_", " ")}</span>
                <span className="mt-1 block text-lg font-medium">{formatMs(value)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-muted-foreground">
            Documentos con modelo {(metrics.llm_usage_ratio * 100).toFixed(1)}%. Error del modelo {(metrics.llm_error_rate * 100).toFixed(1)}%. Tokens {metrics.tokens_input_total} entrada / {metrics.tokens_output_total} salida.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">{metrics.scope}</p>
        </>
      ) : null}
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <li className="rounded-2xl border border-border bg-card px-4 py-4">
      <span className="block text-xs text-muted-foreground">{label}</span>
      <span className="mt-1 block text-2xl font-semibold tracking-tight">{value}</span>
      {hint ? <span className="mt-1 block text-xs text-muted-foreground">{hint}</span> : null}
    </li>
  );
}
