import type { Questionnaire } from "@/features/questionnaire/types/questionnaire.types";

export interface FormatCapability {
  extension: string;
  mime_types: string[];
}

export interface Capabilities {
  formats: FormatCapability[];
  max_upload_size_mb: number;
  max_pdf_pages: number;
  ocr_available: boolean;
  llm_available: boolean;
}

export interface WarningItem {
  code: string;
  message: string;
}

export interface ProcessingMetrics {
  request_id: string;
  file_type: string;
  file_size_bytes: number;
  pages_or_sheets: number | null;
  validation_ms: number;
  parsing_ms: number;
  ocr_ms: number;
  deterministic_extraction_ms: number;
  llm_ms: number;
  validation_output_ms: number;
  total_processing_ms: number;
  llm_used: boolean;
  llm_model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  items_detected: number;
  warnings_count: number;
  status: "success" | "partial" | "failed";
  extraction_method: "text" | "ocr" | "llm_text" | "llm_vision";
  confidence_score: number;
}

export interface ExtractionResponse {
  request_id: string;
  status: "success" | "partial";
  questionnaire: Questionnaire;
  metrics: ProcessingMetrics;
  warnings: WarningItem[];
}
