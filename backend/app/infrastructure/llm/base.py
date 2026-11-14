import asyncio
import random
from collections.abc import Awaitable, Callable


class LLMError(Exception):
    def __init__(self, message: str, *, transient: bool = False, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.transient = transient
        self.retry_after = retry_after


class LLMAuthError(LLMError):
    pass


class LLMQuotaError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "El proveedor LLM no respondió a tiempo.") -> None:
        super().__init__(message, transient=True)


class LLMUnavailableError(LLMError):
    def __init__(self, message: str = "El proveedor LLM no está disponible.") -> None:
        super().__init__(message, transient=True)


class LLMInvalidResponseError(LLMError):
    pass


async def with_retries(fn: Callable[[], Awaitable], max_retries: int):
    attempt = 0
    while True:
        try:
            return await fn()
        except LLMError as exc:
            if not exc.transient or attempt >= max_retries:
                raise
            delay = min(8.0, 0.5 * (2**attempt)) + random.random() * 0.5
            if exc.retry_after:
                delay = max(delay, exc.retry_after)
            await asyncio.sleep(delay)
            attempt += 1
