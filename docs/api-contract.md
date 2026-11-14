# Contrato HTTP

Base: `/api/v1`

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/health` | `{"status":"ok","version":"1.0.0"}` |
| GET | `/documents/capabilities` | formatos, tamaño máximo, OCR y LLM |
| POST | `/documents/extract` | multipart `file`, `use_llm`, `force_ocr` |
| GET | `/metrics` | agregados en memoria. Bearer si `METRICS_TOKEN` existe |

Errores:

```json
{"request_id":"...","error":{"code":"NO_QUESTIONS_DETECTED","message":"..."}}
```

| HTTP | Códigos |
| --- | --- |
| 400 | `MISSING_FILE`, `INVALID_REQUEST`, `EMPTY_FILE`, `CORRUPTED_FILE`, `ENCRYPTED_DOCUMENT`, `DOCUMENT_LIMIT_EXCEEDED`, `UNSAFE_ARCHIVE` |
| 413 | `FILE_TOO_LARGE` |
| 415 | `UNSUPPORTED_FORMAT`, `MIME_MISMATCH` |
| 422 | `NO_TEXT_EXTRACTED`, `NO_QUESTIONS_DETECTED` |
| 429 | `TOO_MANY_REQUESTS` |
| 500 | `INTERNAL_ERROR` |
| 503 | `LLM_UNAVAILABLE` |
| 504 | `PROCESSING_TIMEOUT` |

El objeto `questionnaire` conserva los nombres de la prueba. Las métricas viajan al lado, no dentro de ese objeto.

La confianza es un puntaje heurístico entre 0 y 1. No es una probabilidad calibrada. El umbral por defecto es 0.70.
