import type { Questionnaire } from "@/features/questionnaire/types/questionnaire.types";

export function downloadQuestionnaire(questionnaire: Questionnaire, filename: string) {
  const name = filename.endsWith(".json") ? filename : `${filename}.json`;
  saveFile(new Blob([JSON.stringify(questionnaire, null, 2)], { type: "application/json" }), name);
}

export function downloadAnswersPdf(questionnaire: Questionnaire, filename: string) {
  const name = filename.endsWith(".pdf") ? filename : `${filename}.pdf`;
  const bytes = buildAnswersPdf(questionnaire);
  const copy = new ArrayBuffer(bytes.byteLength);
  new Uint8Array(copy).set(bytes);
  saveFile(new Blob([copy], { type: "application/pdf" }), name);
}

function saveFile(blob: Blob, filename: string) {
  const file = new File([blob], filename, { type: blob.type });
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  window.setTimeout(() => {
    link.remove();
    URL.revokeObjectURL(url);
  }, 1500);
}

const TYPE_LABEL: Record<Questionnaire["items"][number]["tipo"], string> = {
  escala_likert: "Escala Likert",
  seleccion_multiple: "Selección múltiple",
  verdadero_falso: "Verdadero o falso",
  desarrollo: "Desarrollo",
  emparejamiento: "Emparejamiento",
};

function buildAnswersPdf(questionnaire: Questionnaire): Uint8Array {
  const pages: string[][] = [];
  let page: string[] = [];
  let y = 0;
  let pageNumber = 0;

  function openPage() {
    pageNumber += 1;
    page = [];
    pages.push(page);
    page.push("0.145 0.388 0.922 rg");
    page.push("0 786 595 56 re f");
    text(page, "F2", 16, 48, 816, "1 1 1", clip(questionnaire.titulo, 48));
    text(page, "F1", 9, 48, 798, "0.82 0.90 1", "Questionnaire Intelligence");
    text(page, "F1", 9, 430, 798, "0.82 0.90 1", clip(`${questionnaire.idioma} · ${questionnaire.total_items} ítems`, 28));
    page.push("0.89 0.91 0.93 RG");
    page.push("48 46 m 547 46 l S");
    text(page, "F1", 9, 48, 32, "0.28 0.33 0.41", `Página ${pageNumber}`);
    y = 760;
  }

  function ensure(height: number) {
    if (y - height < 64) openPage();
  }

  openPage();
  questionnaire.items.forEach((item, index) => {
    const stem = wrap(`${item.numero}. ${item.enunciado}`, 78);
    const options = item.alternativas.map((option) => ({
      line: wrap(`${option.valor}   ${option.texto}`, 72),
      marked:
        item.respuesta_correcta !== null &&
        String(option.valor).toLowerCase() === String(item.respuesta_correcta).toLowerCase(),
    }));
    const height = 28 + stem.length * 16 + options.reduce((sum, option) => sum + option.line.length * 16 + (option.marked ? 14 : 0), 0) + 18;
    ensure(height);
    if (index > 0) {
      page.push("0.89 0.91 0.93 RG");
      page.push(`48 ${y + 8} m 547 ${y + 8} l S`);
    }
    text(page, "F1", 9, 48, y, "0.145 0.388 0.922", TYPE_LABEL[item.tipo].toUpperCase());
    y -= 16;
    for (const line of stem) {
      text(page, "F2", 12, 48, y, "0.059 0.090 0.165", line);
      y -= 16;
    }
    y -= 4;
    if (options.length === 0) {
      text(page, "F1", 11, 48, y, "0.28 0.33 0.41", "Pregunta abierta. El documento no indica una respuesta.");
      y -= 16;
    }
    for (const option of options) {
      for (const [lineIndex, line] of option.line.entries()) {
        if (option.marked) {
          page.push("0.937 0.965 1 rg");
          page.push(`42 ${y - 4} 505 18 re f`);
        }
        text(page, option.marked ? "F2" : "F1", 11, 48, y, option.marked ? "0.12 0.25 0.56" : "0.059 0.090 0.165", line);
        y -= 16;
        if (option.marked && lineIndex === option.line.length - 1) {
          text(page, "F1", 8, 64, y, "0.12 0.25 0.56", "Respuesta indicada en el documento");
          y -= 14;
        }
      }
    }
    if (item.respuesta_correcta === null && options.length > 0) {
      text(page, "F1", 10, 48, y, "0.28 0.33 0.41", "El documento no indica la respuesta.");
      y -= 14;
    }
    y -= 14;
  });
  return renderPdf(pages);
}

function wrap(value: string, width: number): string[] {
  const words = value.split(/\s+/).filter(Boolean);
  const rows: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > width && current) {
      rows.push(current);
      current = word;
    } else current = next;
  }
  if (current) rows.push(current);
  return rows.length > 0 ? rows : [""];
}

function clip(value: string, width: number): string {
  return value.length <= width ? value : `${value.slice(0, width - 3)}...`;
}

function text(page: string[], font: "F1" | "F2", size: number, x: number, y: number, color: string, value: string) {
  page.push(`${color} rg`);
  page.push(`BT /${font} ${size} Tf ${x} ${y} Td (${pdfString(value)}) Tj ET`);
}

function pdfString(value: string): string {
  let out = "";
  for (const char of value) {
    const code = char.codePointAt(0) ?? 63;
    if (char === "\\") out += "\\\\";
    else if (char === "(") out += "\\(";
    else if (char === ")") out += "\\)";
    else if (code >= 32 && code <= 126) out += char;
    else if (code > 159 && code <= 255) out += `\\${code.toString(8).padStart(3, "0")}`;
    else out += "?";
  }
  return out;
}

function renderPdf(pages: string[][]): Uint8Array {
  const objects: string[] = [];
  const pageIds: number[] = [];
  let next = 5;
  for (const commands of pages) {
    const contentId = next++;
    const pageId = next++;
    pageIds.push(pageId);
    const stream = commands.join("\n");
    objects[contentId] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;
    objects[pageId] =
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentId} 0 R >>`;
  }
  objects[1] = `<< /Type /Catalog /Pages 2 0 R >>`;
  objects[2] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`;
  objects[3] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>`;
  objects[4] = `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>`;
  let body = "%PDF-1.4\n";
  const offsets = [0];
  for (let id = 1; id < objects.length; id += 1) {
    if (!objects[id]) continue;
    offsets[id] = body.length;
    body += `${id} 0 obj\n${objects[id]}\nendobj\n`;
  }
  const xref = body.length;
  let table = `xref\n0 ${objects.length}\n0000000000 65535 f \n`;
  for (let id = 1; id < objects.length; id += 1) {
    table += `${String(offsets[id] ?? 0).padStart(10, "0")} 00000 n \n`;
  }
  body += `${table}trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return new TextEncoder().encode(body);
}
