# Plan: Telegram configurable alerts

## Context
Make Telegram notifications opt-in per event type (`stop`, `milestone`, `done`) via a new `telegram_alerts` config list, replacing the always-on stop-only behavior.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Config

- [x] **Task 1: Add `telegram_alerts` field to config**
  Files: `orchestrator/config.py`
  Import `field` from `dataclasses` (`from dataclasses import dataclass, field`). Add `telegram_alerts: list[str] = field(default_factory=list)` to `OrchestratorConfig` (after the existing telegram fields). In `load_config()`, add `telegram_alerts=data.get("telegram_alerts") or [],` to the `OrchestratorConfig(...)` constructor. Do NOT add it to the `required` list — it stays optional with `.get()`.

- [x] **Task 2: Add `telegram_alerts` to config example** (depends on Task 1)
  Files: `orchestrator.json.example`
  Add `"telegram_alerts": []` as the last key (after `telegram_chat_id`). Keep valid JSON.

### Phase 2: Notify helper

- [x] **Task 3: Add `notify()` to notify module** (depends on Task 1)
  Files: `orchestrator/notify.py`
  Add a `notify(config, text, alert_type)` function above or below `send_telegram`. It must: return early if `alert_type not in config.telegram_alerts`; return early if `config.telegram_bot_token` or `config.telegram_chat_id` is falsy; otherwise call `send_telegram(config.telegram_bot_token, config.telegram_chat_id, text)`. Add a `TYPE_CHECKING` import for `OrchestratorConfig` (`if TYPE_CHECKING: from .config import OrchestratorConfig`) and annotate the `config` param as `"OrchestratorConfig"`. Keep `send_telegram` unchanged.

### Phase 3: Wire call sites in main.py

- [x] **Task 4: Import `notify` and convert stop alerts** (depends on Task 3)
  Files: `orchestrator/main.py`
  Update the import on line 15 from `from .notify import send_telegram` to `from .notify import notify, send_telegram` (or drop `send_telegram` if no longer used after this task — verify it has no other references). In `cli()` (lines ~751–774), replace both inline `if config.telegram_bot_token and config.telegram_chat_id: send_telegram(...)` blocks with single calls: for `PipelineStopError` → `notify(config, f"Orchestrator stopped: {project_dir.name}\n{msg}", "stop")`; for `RateLimitError` → `notify(config, f"Orchestrator rate-limited: {project_dir.name}\n{msg}", "stop")`. Keep the existing `msg = str(e).splitlines()[0]` (first line only).

- [x] **Task 5: Add milestone alert on success paths** (depends on Task 3)
  Files: `orchestrator/main.py`
  In `process_milestone()` add `notify(config, f"Milestone done: {milestone.title}\nProject: {project_dir.name}", "milestone")` after both success-path `_git_commit(project_dir, milestone.title)` calls (the resume `step == "done"` branch at line ~281 and the normal completion at line ~386). In `process_test_milestone()` add the same call after both `_git_commit(...)` success-path calls (lines ~523 and ~629). Do NOT add it to any `mark_skipped()` path.

- [x] **Task 6: Add done alert when queue is empty** (depends on Task 3)
  Files: `orchestrator/main.py`
  In `_run_dynamic_loop()`, in the `while` loop where `if not pending: break` (line ~661), add `notify(config, f"All milestones done: {project_dir.name}", "done")` before the `break`. Leave the pre-loop startup `if not pending` check (line ~645) unchanged.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Add telegram_alerts config and notify helper"
- **Commit 2** (after tasks 4-6): "Wire configurable telegram alerts into orchestrator call sites"
