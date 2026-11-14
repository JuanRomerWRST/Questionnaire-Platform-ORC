"use client";

import { Button } from "@/components/ui/Button";
import { downloadQuestionnaire } from "@/features/export/services/export.service";
import type { Questionnaire } from "@/features/questionnaire/types/questionnaire.types";

export function DownloadJsonButton({ questionnaire }: { questionnaire: Questionnaire }) {
  return (
    <Button
      type="button"
      onClick={() => downloadQuestionnaire(questionnaire, "cuestionario.json")}
    >
      Descargar JSON
    </Button>
  );
}
