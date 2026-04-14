"""Send digests to Telegram."""

from __future__ import annotations

import os

import requests


def send_digest(message: str, chat_id: str | None = None, token: str | None = None) -> bool:
    """Send a digest message to Telegram.

    Args:
        message: The formatted message to send
        chat_id: Telegram chat ID (defaults to env var)
        token: Telegram bot token (defaults to env var)

    Returns:
        True if sent successfully
    """
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False
