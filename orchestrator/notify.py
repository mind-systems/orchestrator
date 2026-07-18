"""Notification helpers — stdlib only, no new dependencies."""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import OrchestratorConfig


# Alert types that report a task failure rather than a success.
_FAIL_ALERTS = {"milestone-fail"}

# Alert types that report an operational stop — not a task failure.
_HALT_ALERTS = {"stop"}


def notify(config: "OrchestratorConfig", text: str, alert_type: str) -> None:
    """Send a Telegram notification if alert_type is listed in config.telegram_alerts."""
    if alert_type not in config.telegram_alerts:
        return
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return
    emoji = "🔴" if alert_type in _FAIL_ALERTS else "🟡" if alert_type in _HALT_ALERTS else "🟢"
    send_telegram(config.telegram_bot_token, config.telegram_chat_id, f"{emoji} {text}")


def send_telegram(token: str, chat_id: str, text: str) -> None:
    """POST a message to a Telegram chat via the Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(url, data=payload, timeout=10)
    except Exception as e:
        print(f"  [telegram] notification failed: {e}")
