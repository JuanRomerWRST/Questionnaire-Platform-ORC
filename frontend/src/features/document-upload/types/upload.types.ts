export type ProcessState =
  | "idle"
  | "selected"
  | "validating"
  | "uploading"
  | "processing"
  | "success"
  | "partial"
  | "error"
  | "rate_limited";
