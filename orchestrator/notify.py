"""Notification helpers — stdlib only, no new dependencies."""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request


def send_telegram(token: str, chat_id: str, text: str) -> None:
    """POST a message to a Telegram chat via the Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(url, data=payload, timeout=10)
    except Exception as e:
        print(f"  [telegram] notification failed: {e}")
