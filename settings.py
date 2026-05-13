"""
config/settings.py
Centralized configuration and environment variable loading.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Providers
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    PRIMARY_PROVIDER: str = os.getenv("PRIMARY_PROVIDER", "openai")
    FALLBACK_PROVIDERS: list[str] = [
        p.strip() for p in os.getenv("FALLBACK_PROVIDERS", "anthropic").split(",") if p.strip()
    ]

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_USER_IDS: list[int] = [
        int(uid.strip())
        for uid in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
        if uid.strip().isdigit()
    ]

    # Agent behavior
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "2"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    STREAMING_ENABLED: bool = os.getenv("STREAMING_ENABLED", "true").lower() == "true"

    # Reliability agent
    RELIABILITY_CHECK_INTERVAL: int = int(os.getenv("RELIABILITY_CHECK_INTERVAL", "300"))
    RELIABILITY_LOG_PATH: str = os.getenv("RELIABILITY_LOG_PATH", "logs/reliability.log")

    # Cost tracking
    COST_TRACKING_ENABLED: bool = os.getenv("COST_TRACKING_ENABLED", "true").lower() == "true"
    DAILY_SPEND_ALERT_USD: float = float(os.getenv("DAILY_SPEND_ALERT_USD", "50.0"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH: str = os.getenv("LOG_PATH", "logs/agent.log")


settings = Settings()
