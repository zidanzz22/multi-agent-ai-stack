"""
agents/task_agent.py
Task automation agent — handles scheduled and on-demand automation tasks.
Supports both OpenAI and Anthropic backends with automatic failover.
"""

import asyncio
import logging

import openai
import anthropic

from config.settings import settings
from core.self_healing import with_retry, RateLimitError, AuthError, map_http_error

logger = logging.getLogger(__name__)

openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a precise task automation agent. 
When given a task, break it into clear steps and execute or describe each one explicitly.
Be concise, structured, and always confirm task completion."""


@with_retry()
async def call_openai(prompt: str, streaming: bool = False) -> str:
    try:
        if streaming:
            return await _stream_openai(prompt)
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=settings.MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            timeout=settings.REQUEST_TIMEOUT,
        )
        return response.choices[0].message.content or ""
    except openai.AuthenticationError as e:
        raise AuthError(str(e))
    except openai.RateLimitError as e:
        raise RateLimitError(str(e))
    except openai.APIStatusError as e:
        raise map_http_error(e.status_code, str(e))


async def _stream_openai(prompt: str) -> str:
    """Stream from OpenAI and collect full response."""
    chunks = []
    async with openai_client.chat.completions.stream(
        model="gpt-4o",
        max_tokens=settings.MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    ) as stream:
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                chunks.append(delta)
    return "".join(chunks)


@with_retry()
async def call_anthropic(prompt: str, **kwargs) -> str:
    try:
        response = await anthropic_client.messages.create(
            model="claude-opus-4-5",
            max_tokens=settings.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""
    except anthropic.AuthenticationError as e:
        raise AuthError(str(e))
    except anthropic.RateLimitError as e:
        raise RateLimitError(str(e))
    except anthropic.APIStatusError as e:
        raise map_http_error(e.status_code, str(e))


async def run(prompt: str, streaming: bool = False) -> str:
    """Entry point for the task agent."""
    logger.info(f"[TaskAgent] Running task: {prompt[:80]}...")
    # Try primary provider, fallback handled by orchestrator/router
    if settings.PRIMARY_PROVIDER == "openai":
        return await call_openai(prompt, streaming=streaming)
    return await call_anthropic(prompt)


if __name__ == "__main__":
    result = asyncio.run(run("List the steps to back up a PostgreSQL database."))
    print(result)
