import asyncio

import pytest

from app.infrastructure.llm.base import LLMError, LLMQuotaError, with_retries
from app.infrastructure.llm.openai_provider import _map_error


class RateLimitError(Exception):
    code = "rate_limit_exceeded"


def test_empty_balance_is_not_called_a_rate_limit():
    class RateLimitError(Exception):
        code = "credit_balance_exhausted"

    error = _map_error(RateLimitError("You have no credits remaining."))
    assert isinstance(error, LLMQuotaError)
    assert "saldo" in str(error)


def test_rate_limit_is_not_marked_for_retry():
    error = _map_error(RateLimitError("slow down"))
    assert isinstance(error, LLMError)
    assert error.transient is False
    assert str(error) == "OpenAI aplicó un límite de tasa."


def test_a_rate_limit_stops_after_one_call():
    calls = 0

    async def fail():
        nonlocal calls
        calls += 1
        raise _map_error(RateLimitError("slow down"))

    async def run():
        with pytest.raises(LLMError, match="límite de tasa"):
            await with_retries(fail, 2)

    asyncio.run(run())
    assert calls == 1
