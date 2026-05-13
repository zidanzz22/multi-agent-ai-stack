"""
core/self_healing.py
Retry logic, exponential backoff, and silent failure detection.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any

from config.settings import settings

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Raised when a provider fails in a non-retryable way."""
    pass


class RateLimitError(Exception):
    """Raised on HTTP 429 rate limit responses."""
    pass


class AuthError(Exception):
    """Raised on HTTP 401 authentication failures."""
    pass


def with_retry(
    max_retries: int = None,
    base_delay: float = None,
    retryable_exceptions: tuple = (RateLimitError, TimeoutError, ConnectionError),
):
    """
    Decorator: retry an async function with exponential backoff.
    Skips retry on AuthError and ProviderError (non-retryable).
    """
    max_retries = max_retries or settings.MAX_RETRIES
    base_delay = base_delay or settings.RETRY_BASE_DELAY

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    _validate_response(result)
                    return result
                except (AuthError, ProviderError) as e:
                    # Non-retryable — fail immediately
                    logger.error(f"[{func.__name__}] Non-retryable error: {e}")
                    raise
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"[{func.__name__}] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"[{func.__name__}] All {max_retries} retries exhausted.")
                        raise last_exception
        return wrapper
    return decorator


def _validate_response(response: Any) -> None:
    """
    Detect silent failures: empty, None, or malformed LLM responses.
    Raises ValueError if the response looks broken.
    """
    if response is None:
        raise ValueError("Silent failure: LLM returned None")
    if isinstance(response, str) and not response.strip():
        raise ValueError("Silent failure: LLM returned empty string")
    if isinstance(response, dict):
        content = response.get("content") or response.get("choices")
        if not content:
            raise ValueError(f"Silent failure: malformed response structure: {response}")


def map_http_error(status_code: int, message: str = "") -> Exception:
    """Convert HTTP status codes to typed exceptions."""
    if status_code == 401:
        return AuthError(f"Authentication failed (401): {message}")
    if status_code == 429:
        return RateLimitError(f"Rate limited (429): {message}")
    if status_code >= 500:
        return ProviderError(f"Provider server error ({status_code}): {message}")
    return ProviderError(f"Unexpected error ({status_code}): {message}")
