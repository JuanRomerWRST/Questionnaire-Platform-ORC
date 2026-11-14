"use client";

import { useState } from "react";

export function useFileUpload() {
  const [file, setFile] = useState<File | null>(null);
  return { file, setFile };
}
