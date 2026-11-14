from pathlib import PurePath

from fastapi import UploadFile

from app.core.exceptions import AppError


def safe_extension(filename: str | None) -> str:
    name = PurePath(filename or "").name
    suffix = PurePath(name).suffix.lower()
    if not suffix or "/" in name or "\\" in name or ".." in PurePath(name).parts:
        return suffix
    return suffix


async def read_upload_limited(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise AppError(413, "FILE_TOO_LARGE", "El archivo supera el tamaño máximo permitido.")
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise AppError(400, "EMPTY_FILE", "El archivo está vacío.")
    return data
