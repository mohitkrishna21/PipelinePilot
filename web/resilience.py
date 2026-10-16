import asyncio
import openai

from openai import AsyncOpenAI
from agents import set_default_openai_client


def configure_openai(settings) -> None:
    client = AsyncOpenAI(
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries
    )

    set_default_openai_client(client)


def friendly_error(exc) -> str:

    # 1. OpenAI quota exhausted
    if (
        isinstance(exc, openai.RateLimitError)
        and getattr(exc, "code", None) == "insufficient_quota"
    ):
        return (
            "The demo has reached its usage limit for now. "
            "Please check back later."
        )

    # 2. OpenAI rate limit
    if isinstance(exc, openai.RateLimitError):
        return (
            "The AI service is busy right now. "
            "Please try again in a minute."
        )

    # 3. Request or turn timeout
    if isinstance(
        exc,
        (openai.APITimeoutError, asyncio.TimeoutError)
    ):
        return (
            "That took too long. Try a shorter message, "
            "or try again."
        )

    # 4. Connection failure
    if isinstance(exc, openai.APIConnectionError):
        return (
            "I can't reach the AI service right now. "
            "Please try again shortly."
        )

    # 5. Other OpenAI API errors
    if isinstance(exc, openai.APIStatusError):
        return "The demo is temporarily unavailable."

    # 6. Unknown error
    return "Something went wrong. Please try again."
