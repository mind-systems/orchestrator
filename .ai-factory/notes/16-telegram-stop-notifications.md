# Telegram Stop Notifications

**Date:** 2026-06-19
**Source:** conversation context

## Key Findings

- Orchestrator stops silently on two failure conditions — max iterations exceeded and session usage threshold breached — with no external signal; user must watch the terminal.
- Both conditions surface as `PipelineStopError` caught in `cli()` in `main.py`; `RateLimitError` is caught in the same `except` chain and should also notify.
- Telegram credentials (`bot_token`, `chat_id`) belong in `orchestrator.json` as optional fields — absent or empty means no-op, no error.
- `urllib.request` (stdlib) is sufficient; no new dependency needed.

## Details

### Files to touch

| File | Change |
|------|--------|
| `orchestrator/config.py` | Add two optional dataclass fields; read them in `load_config()` via `.get()` (not in `required` list) |
| `orchestrator/notify.py` | New module — `send_telegram(token, chat_id, text)` |
| `orchestrator/main.py` | Call `send_telegram` in `cli()` exception handlers |
| `orchestrator.json.example` | Add the two new optional keys with empty-string defaults |

### `OrchestratorConfig` change (`config.py`)

```python
@dataclass
class OrchestratorConfig:
    max_iterations: int
    usage_threshold_5h: float
    usage_threshold_weekly: float
    enable_phase_sessions: bool
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
```

In `load_config()`, after building the dataclass:
```python
    telegram_bot_token=data.get("telegram_bot_token") or None,
    telegram_chat_id=data.get("telegram_chat_id") or None,
```
`or None` coerces empty string `""` to `None` so callers only need to check truthiness.

Do NOT add the two keys to `required` — they are optional.

### `notify.py`

```python
"""Telegram notification sender for orchestrator status changes."""
from __future__ import annotations
import urllib.error, urllib.parse, urllib.request

def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(url, data=payload, timeout=10)
    except Exception as e:
        print(f"  [telegram] notification failed: {e}")
```

### `cli()` change (`main.py`)

Import `send_telegram` at the top. In the two `except` blocks:

```python
    except PipelineStopError as e:
        msg = str(e).splitlines()[0]  # first line only — avoid huge dumps
        print(f"\n{'='*60}")
        print(f"STOPPED — {e}")
        print(f"{'='*60}")
        if config.telegram_bot_token and config.telegram_chat_id:
            send_telegram(
                config.telegram_bot_token,
                config.telegram_chat_id,
                f"Orchestrator stopped: {project_dir.name}\nReason: {msg}",
            )
        sys.exit(0)
    except RateLimitError as e:
        msg = str(e).splitlines()[0]
        print(f"\n{'='*60}")
        print(f"STOPPED — Claude rate limit reached: {e}")
        print(f"{'='*60}")
        if config.telegram_bot_token and config.telegram_chat_id:
            send_telegram(
                config.telegram_bot_token,
                config.telegram_chat_id,
                f"Orchestrator rate-limited: {project_dir.name}\nReason: {msg}",
            )
        sys.exit(0)
```

`project_dir` is already in scope in `cli()` at the point of both catches.

### `orchestrator.json.example` addition

```json
{
  "max_iterations": 3,
  "usage_threshold_5h": 90,
  "usage_threshold_weekly": 95,
  "enable_phase_sessions": false,
  "telegram_bot_token": "",
  "telegram_chat_id": ""
}
```

### Guard conditions

- Both fields must be truthy to send — one missing means silent skip.
- `send_telegram` never raises — logs to stdout on failure.
- First line of error message only in notification — avoids sending the full review file dump to Telegram.

### How to verify

1. Add `telegram_bot_token` and `telegram_chat_id` to `orchestrator.json`.
2. Set `max_iterations: 1` and run on a task the planner will not pass on first plan review.
3. Orchestrator raises `PipelineStopError` → Telegram message arrives with project name and reason.
4. Remove or blank out `telegram_bot_token` → no message sent, no error.
