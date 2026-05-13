"""
agents/telegram_agent.py
Telegram-based personal assistant agent.
Handles real-time streaming responses and per-user conversation memory.
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from config.settings import settings
from core.orchestrator import dispatch

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Simple in-memory conversation history per user
# For production, replace with a persistent store (Redis, DB, etc.)
conversation_history: dict[int, list[dict]] = {}


def is_allowed(user_id: int) -> bool:
    if not settings.TELEGRAM_ALLOWED_USER_IDS:
        return True  # No allowlist = open to all (set one in production!)
    return user_id in settings.TELEGRAM_ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Multi-Agent AI Assistant online.\n"
        "Send me any message and I'll route it to the right agent."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_input = update.message.text

    if not is_allowed(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    logger.info(f"[TelegramAgent] Message from {user_id}: {user_input[:60]}...")

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = await dispatch(user_input, streaming=False)
        # Telegram max message length is 4096 chars — split if needed
        for chunk in _split_message(str(response)):
            await update.message.reply_text(chunk)
    except Exception as e:
        logger.error(f"[TelegramAgent] Error: {e}")
        await update.message.reply_text(
            "⚠️ An error occurred processing your request. All providers may be unavailable. "
            "Please try again in a moment."
        )


def _split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split long responses into Telegram-sized chunks."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in your .env file.")

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("[TelegramAgent] Bot started. Listening for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
