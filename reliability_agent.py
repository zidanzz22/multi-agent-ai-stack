"""
agents/reliability_agent.py
Provider reliability testing agent.
Continuously monitors LLM provider uptime, latency, and response quality.
Logs results and updates the provider pool accordingly.
"""

import asyncio
import logging
import time

from config.settings import settings
from core.self_healing import AuthError, ProviderError

logger = logging.getLogger(__name__)

TEST_PROMPT = "Reply with exactly: OK"
EXPECTED_RESPONSE_SUBSTRING = "OK"


async def ping_openai() -> dict:
    """Test OpenAI availability and measure latency."""
    import openai
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    start = time.monotonic()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            timeout=10,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        content = response.choices[0].message.content or ""
        ok = EXPECTED_RESPONSE_SUBSTRING in content
        return {"provider": "openai", "healthy": ok, "latency_ms": latency_ms, "response": content}
    except Exception as e:
        return {"provider": "openai", "healthy": False, "error": str(e)}


async def ping_anthropic() -> dict:
    """Test Anthropic availability and measure latency."""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    start = time.monotonic()
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": TEST_PROMPT}],
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        content = response.content[0].text if response.content else ""
        ok = EXPECTED_RESPONSE_SUBSTRING in content
        return {"provider": "anthropic", "healthy": ok, "latency_ms": latency_ms, "response": content}
    except Exception as e:
        return {"provider": "anthropic", "healthy": False, "error": str(e)}


async def run_checks() -> list[dict]:
    """Run all provider health checks in parallel."""
    results = await asyncio.gather(ping_openai(), ping_anthropic(), return_exceptions=True)
    checked = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[ReliabilityAgent] Check raised exception: {r}")
        else:
            status = "✅" if r["healthy"] else "❌"
            latency = r.get("latency_ms", "N/A")
            logger.info(f"[ReliabilityAgent] {status} {r['provider']} — {latency}ms")
            checked.append(r)

            # Update provider pool based on results
            from core.provider_router import pool
            if r["healthy"]:
                pool.mark_healthy(r["provider"])
            else:
                pool.mark_failed(r["provider"])

    return checked


async def run(prompt: str = "") -> str:
    """Entry point called by the orchestrator for reliability queries."""
    results = await run_checks()
    lines = []
    for r in results:
        if r["healthy"]:
            lines.append(f"✅ {r['provider']}: healthy ({r.get('latency_ms')}ms)")
        else:
            lines.append(f"❌ {r['provider']}: DOWN — {r.get('error', 'unknown error')}")
    return "\n".join(lines) if lines else "No providers checked."


async def continuous_monitor() -> None:
    """Run health checks on a schedule indefinitely."""
    logger.info(f"[ReliabilityAgent] Starting continuous monitoring every {settings.RELIABILITY_CHECK_INTERVAL}s")
    while True:
        await run_checks()
        await asyncio.sleep(settings.RELIABILITY_CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(continuous_monitor())
