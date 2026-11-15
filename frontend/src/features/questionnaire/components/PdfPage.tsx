"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy } from "pdfjs-dist";

let library: Promise<typeof import("pdfjs-dist")> | null = null;
const documents = new Map<string, Promise<PDFDocumentProxy>>();

function loadLibrary() {
  library ??= import("pdfjs-dist").then((pdfjs) => {
    pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";
    return pdfjs;
  });
  return library;
}

function loadDocument(url: string) {
  const cached = documents.get(url);
  if (cached) return cached;
  const pending = (async () => {
    const pdfjs = await loadLibrary();
    const data = await fetch(url).then((response) => response.arrayBuffer());
    return pdfjs.getDocument({ data }).promise;
  })();
  documents.set(url, pending);
  pending.catch(() => documents.delete(url));
  return pending;
}

export function PdfPage({ url, pageNumber }: { url: string; pageNumber: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [failed, setFailed] = useState("");

  useEffect(() => {
    let cancel = false;
    (async () => {
      const pdf = await loadDocument(url);
      const page = await pdf.getPage(pageNumber);
      if (cancel) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const width = canvas.parentElement?.clientWidth || 720;
      const unscaled = page.getViewport({ scale: 1 });
      const viewport = page.getViewport({ scale: Math.max(1, width / unscaled.width) });
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const context = canvas.getContext("2d");
      if (!context) return;
      await page.render({ canvasContext: context, canvas, viewport }).promise;
    })().catch((error: unknown) => {
      console.error(error);
      if (!cancel) setFailed("No se pudo pintar esta página.");
    });
    return () => {
      cancel = true;
    };
  }, [pageNumber, url]);

  if (failed) {
    return <p className="p-4 text-sm text-muted-foreground">{failed}</p>;
  }

  return <canvas ref={canvasRef} aria-label={`Página ${pageNumber}`} className="block w-full bg-white" />;
}
