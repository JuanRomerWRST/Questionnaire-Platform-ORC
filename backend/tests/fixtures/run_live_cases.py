"""Corre los casos visuales y de baja confianza contra la API local.

No imprime secretos. Guarda el cuestionario y un informe corto en docs/examples/output/live.
"""

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3] / "docs" / "examples"
API = "http://127.0.0.1:8000/api/v1/documents/extract"


def main() -> None:
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    live = [case for case in cases if case["mode"] in {"ocr", "llm", "ocr_llm"}]
    target = ROOT / "output" / "live"
    target.mkdir(parents=True, exist_ok=True)
    summary = []
    with httpx.Client(timeout=120) as client:
        for case in live:
            use_llm = "false" if case["mode"] == "ocr" else "true"
            path = ROOT / "input" / case["file"]
            response = client.post(
                API,
                files={"file": (case["file"], path.read_bytes())},
                data={"use_llm": use_llm},
            )
            body = response.json()
            stem = Path(case["file"]).stem
            if response.status_code >= 400:
                report = {"file": case["file"], "mode": case["mode"], "status": response.status_code, "error": body}
            else:
                (target / f"{stem}.json").write_text(
                    json.dumps(body["questionnaire"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                report = {
                    "file": case["file"],
                    "mode": case["mode"],
                    "http": response.status_code,
                    "status": body["status"],
                    "extraction_method": body["metrics"]["extraction_method"],
                    "llm_used": body["metrics"]["llm_used"],
                    "llm_model": body["metrics"]["llm_model"],
                    "ocr_ms": body["metrics"]["ocr_ms"],
                    "llm_ms": body["metrics"]["llm_ms"],
                    "items": body["metrics"]["items_detected"],
                    "confidence": body["metrics"]["confidence_score"],
                    "warnings": [warning["code"] for warning in body["warnings"]],
                }
            (target / f"{stem}.report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            summary.append(report)
            print(json.dumps(report, ensure_ascii=False))
    (target / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
