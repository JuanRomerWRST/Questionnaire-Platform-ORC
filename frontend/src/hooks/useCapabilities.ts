"use client";

import { useEffect, useState } from "react";
import { getCapabilities } from "@/lib/api-client";
import { FALLBACK_FORMATS, FALLBACK_MAX_MB } from "@/lib/constants";
import type { Capabilities } from "@/types/api.types";

const fallback: Capabilities = {
  formats: FALLBACK_FORMATS.map((extension) => ({ extension, mime_types: [] })),
  max_upload_size_mb: FALLBACK_MAX_MB,
  max_pdf_pages: 100,
  ocr_available: false,
  llm_available: false,
};

export function useCapabilities() {
  const [capabilities, setCapabilities] = useState<Capabilities>(fallback);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    getCapabilities()
      .then((value) => {
        setCapabilities(value);
        setOffline(false);
      })
      .catch(() => setOffline(true));
  }, []);

  return { capabilities, offline };
}
