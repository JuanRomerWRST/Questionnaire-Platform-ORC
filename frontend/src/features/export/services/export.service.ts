import type { Questionnaire } from "@/features/questionnaire/types/questionnaire.types";

export function downloadQuestionnaire(questionnaire: Questionnaire, filename: string) {
  const blob = new Blob([JSON.stringify(questionnaire, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".json") ? filename : `${filename}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
