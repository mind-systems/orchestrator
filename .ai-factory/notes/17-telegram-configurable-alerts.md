# Telegram Configurable Alerts

**Date:** 2026-06-20
**Source:** conversation context

## Key Findings

- Three alert types: `"stop"` (any error-stop), `"milestone"` (successful milestone done), `"done"` (all milestones finished).
- Config array `telegram_alerts` controls which types fire — empty array = no notifications.
- `config` is already a parameter of `process_milestone`, `process_test_milestone`, and `_run_dynamic_loop`, so no signature changes needed.
- `notify.py` exposes two functions: low-level `send_telegram` and high-level `notify(config, text, alert_type)` that handles the type check and credential guard.

## Details

### Files to touch

| File | Change |
|------|--------|
| `orchestrator/config.py` | Add `telegram_alerts: list[str]` field; import `field` from dataclasses; read via `.get()` in `load_config()` |
| `orchestrator/notify.py` | New module — `send_telegram` + `notify` |
| `orchestrator/main.py` | Three call sites: `cli()` exceptions, `process_milestone()` after commit, `_run_dynamic_loop()` on empty pending |
| `orchestrator.json.example` | Add three new keys |

### `OrchestratorConfig` change (`config.py`)

```python
from dataclasses import dataclass, field

@dataclass
class OrchestratorConfig:
    max_iterations: int
    usage_threshold_5h: float
    usage_threshold_weekly: float
    enable_phase_sessions: bool
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_alerts: list[str] = field(default_factory=list)
```

In `load_config()` (not in `required` list):
```python
    telegram_bot_token=data.get("telegram_bot_token") or None,
    telegram_chat_id=data.get("telegram_chat_id") or None,
    telegram_alerts=data.get("telegram_alerts") or [],
```

### `notify.py`

```python
"""Telegram notification sender for orchestrator status changes."""
from __future__ import annotations
import urllib.error, urllib.parse, urllib.request
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .config import OrchestratorConfig


def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(url, data=payload, timeout=10)
    except Exception as e:
        print(f"  [telegram] notification failed: {e}")


def notify(config: "OrchestratorConfig", text: str, alert_type: str) -> None:
    """Send a Telegram message if alert_type is enabled and credentials are set."""
    if alert_type not in config.telegram_alerts:
        return
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return
    send_telegram(config.telegram_bot_token, config.telegram_chat_id, text)
```

### Call sites in `main.py`

**1. `cli()` — stop alerts (both exception types):**

```python
from .notify import notify

    except PipelineStopError as e:
        msg = str(e).splitlines()[0]
        print(...)
        notify(config, f"Orchestrator stopped: {project_dir.name}\n{msg}", "stop")
        sys.exit(0)
    except RateLimitError as e:
        msg = str(e).splitlines()[0]
        print(...)
        notify(config, f"Orchestrator rate-limited: {project_dir.name}\n{msg}", "stop")
        sys.exit(0)
```

Both use `"stop"` — user doesn't need to distinguish.

**2. `process_milestone()` and `process_test_milestone()` — milestone alert:**

After `_git_commit(project_dir, milestone.title)` and before `return`:
```python
    notify(config, f"Milestone done: {milestone.title}\nProject: {project_dir.name}", "milestone")
```

**3. `_run_dynamic_loop()` — done alert:**

The loop already breaks when `pending` is empty. Add notify after the `break`:
```python
        if not pending:
            notify(config, f"All milestones done: {project_dir.name}", "done")
            break
```

### `orchestrator.json.example`

```json
{
  "max_iterations": 3,
  "usage_threshold_5h": 90,
  "usage_threshold_weekly": 95,
  "enable_phase_sessions": false,
  "telegram_bot_token": "",
  "telegram_chat_id": "",
  "telegram_alerts": []
}
```

Users who want all alerts: `["stop", "milestone", "done"]`.

### Guard conditions

- `notify` is a no-op if `alert_type` not in array — zero overhead, no config required.
- `send_telegram` never raises — logs to stdout on network failure.
- First line of error message only in stop notifications — avoids sending full review file dump.
- `process_milestone()` returns early via `mark_skipped()` in two places — those should NOT notify `"milestone"` since the milestone was skipped, not completed.

### How to verify

1. Set `telegram_alerts: ["milestone"]`, run a milestone.
2. Telegram message arrives with title and project name.
3. Set `telegram_alerts: []` — no message on next run.
4. Set `telegram_alerts: ["stop"]`, trigger `PipelineStopError` (e.g. `max_iterations: 1`).
5. Set `telegram_alerts: ["done"]`, let orchestrator finish all milestones.
