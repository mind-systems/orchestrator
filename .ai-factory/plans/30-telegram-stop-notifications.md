# Plan: Telegram stop notifications

## Context
Send an optional Telegram message when the orchestrator halts on `PipelineStopError` or `RateLimitError`, so the user no longer has to watch the terminal. Credentials live in `orchestrator.json` as optional fields; missing/empty means a silent no-op with no new dependencies.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Config

- [x] **Task 1: Add optional Telegram fields to OrchestratorConfig**
  Files: `orchestrator/config.py`
  In the `OrchestratorConfig` dataclass add two optional fields after `enable_phase_sessions`: `telegram_bot_token: str | None = None` and `telegram_chat_id: str | None = None`. In `load_config()`, do NOT add these keys to the `required` list. When constructing the dataclass, read them via `data.get(...) or None` so an empty string `""` is coerced to `None` and callers only need a truthiness check:
  ```python
  telegram_bot_token=data.get("telegram_bot_token") or None,
  telegram_chat_id=data.get("telegram_chat_id") or None,
  ```

- [x] **Task 2: Add Telegram keys to the example config**
  Files: `orchestrator.json.example`
  Add `"telegram_bot_token": ""` and `"telegram_chat_id": ""` as empty-string defaults (keep valid JSON — add a comma after the `enable_phase_sessions` line).

### Phase 2: Notification sender

- [x] **Task 3: Create the notify module**
  Files: `orchestrator/notify.py`
  New stdlib-only module. Define `send_telegram(token: str, chat_id: str, text: str) -> None` that POSTs to `https://api.telegram.org/bot{token}/sendMessage` with `urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()` as the body, using `urllib.request.urlopen(url, data=payload, timeout=10)`. Wrap the request in `try/except Exception` and print a one-line failure notice (`  [telegram] notification failed: {e}`) so a network error never crashes the process. Start the file with `from __future__ import annotations` and import `urllib.error`, `urllib.parse`, `urllib.request`.

### Phase 3: Wire into CLI

- [x] **Task 4: Notify from cli() exception handlers** (depends on Task 1, Task 3)
  Files: `orchestrator/main.py`
  Import `send_telegram` from `.notify` near the other local imports. In `cli()`, inside both the `except PipelineStopError as e:` and `except RateLimitError as e:` blocks (after the existing print statements, before `sys.exit(0)`), compute `msg = str(e).splitlines()[0]` (first line only — avoids dumping full review text). If `config.telegram_bot_token and config.telegram_chat_id` are both truthy, call `send_telegram(config.telegram_bot_token, config.telegram_chat_id, ...)`. Message text:
  - `PipelineStopError`: `f"Orchestrator stopped: {project_dir.name}\nReason: {msg}"`
  - `RateLimitError`: `f"Orchestrator rate-limited: {project_dir.name}\nReason: {msg}"`
  Both `config` and `project_dir` are already in scope at the catch points. If either field is falsy, do nothing (silent no-op).
