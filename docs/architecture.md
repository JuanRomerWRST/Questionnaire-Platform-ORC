# Arquitectura

Monolito modular. El navegador habla con Next.js y envía el archivo directo a FastAPI. No hay base de datos, colas ni almacenamiento de documentos.

```text
Usuario -> Next.js -> POST /api/v1/documents/extract
        -> validación -> parser -> reglas -> confianza
        -> LLM solo si la confianza es baja y está configurado
        -> JSON + métricas
```

No existe `src/app/page.tsx`. La ruta `/` vive en `src/app/(workspace)/page.tsx`. Tener las dos páginas resolvería a la misma ruta y el build de Next fallaría.

Las métricas viven en memoria, en una sola instancia, y se reinician con el proceso.

## Emparejamiento

Un bloque de emparejamiento es un ítem. La columna izquierda usa `valor` entero y la derecha usa `valor` letra. Si el documento trae la clave, `respuesta_correcta` tiene la forma `1-A,2-B`.

## Idioma

`es`, `en`, `it` u otro código ISO 639-1 si la detección local es clara. Si no hay texto suficiente, el valor es `und`.
