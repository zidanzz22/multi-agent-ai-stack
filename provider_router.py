"""
core/provider_router.py
Provider selection, availability tracking, and automatic failover.
"""

import logging
from typing import Optional

from config.settings import settings
from core.self_healing import AuthError, ProviderError

logger = logging.getLogger(__name__)


class ProviderPool:
    """
    Tracks which providers are healthy and routes requests accordingly.
    Automatically removes failed providers and restores them after a cooldown.
    """

    COOLDOWN_SECONDS = 120  # Time before a failed provider is re-tried

    def __init__(self):
        self._providers: list[str] = [settings.PRIMARY_PROVIDER] + settings.FALLBACK_PROVIDERS
        self._failed: dict[str, float] = {}  # provider -> timestamp of failure

    def get_available(self) -> list[str]:
        """Return providers that are currently healthy, in priority order."""
        import time
        now = time.time()
        # Restore providers that have cooled down
        recovered = [p for p, t in self._failed.items() if now - t > self.COOLDOWN_SECONDS]
        for p in recovered:
            logger.info(f"[ProviderPool] {p} recovered after cooldown, restoring to pool.")
            del self._failed[p]
        return [p for p in self._providers if p not in self._failed]

    def mark_failed(self, provider: str) -> None:
        """Flag a provider as unavailable."""
        import time
        logger.warning(f"[ProviderPool] Marking {provider} as failed.")
        self._failed[provider] = time.time()

    def mark_healthy(self, provider: str) -> None:
        """Explicitly restore a provider."""
        if provider in self._failed:
            del self._failed[provider]
            logger.info(f"[ProviderPool] {provider} marked healthy.")


pool = ProviderPool()


async def route_request(prompt: str, task_type: str = "default", **kwargs) -> str:
    """
    Route a prompt to the best available provider.
    Falls through the provider list until one succeeds or all fail.
    """
    available = pool.get_available()

    if not available:
        raise ProviderError("All providers are currently unavailable.")

    last_error: Optional[Exception] = None

    for provider in available:
        try:
            logger.info(f"[Router] Routing '{task_type}' task to {provider}")
            response = await _call_provider(provider, prompt, **kwargs)
            pool.mark_healthy(provider)
            return response
        except AuthError as e:
            logger.error(f"[Router] Auth error on {provider}: {e}")
            pool.mark_failed(provider)
            last_error = e
        except ProviderError as e:
            logger.warning(f"[Router] Provider error on {provider}: {e}. Trying next...")
            pool.mark_failed(provider)
            last_error = e

    raise ProviderError(f"All providers failed. Last error: {last_error}")


async def _call_provider(provider: str, prompt: str, **kwargs) -> str:
    """Dispatch to the correct provider client."""
    if provider == "openai":
        from agents.task_agent import call_openai
        return await call_openai(prompt, **kwargs)
    elif provider == "anthropic":
        from agents.task_agent import call_anthropic
        return await call_anthropic(prompt, **kwargs)
    else:
        raise ProviderError(f"Unknown provider: {provider}")
