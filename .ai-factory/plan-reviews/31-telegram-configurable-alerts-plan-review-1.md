# Plan Review: Telegram configurable alerts

**Plan:** `.ai-factory/plans/31-telegram-configurable-alerts.md`
**Risk Level:** 🟢 Low

## Verification against codebase

All file paths, line numbers, function signatures, and API references in the plan were checked against the current source. They are accurate:

- **Task 1 — `config.py`:** `OrchestratorConfig` is a `@dataclass` with `telegram_bot_token`/`telegram_chat_id` defaulting to `None` (lines 17–18). Adding `telegram_alerts: list[str] = field(default_factory=list)` after them is valid — all non-default fields precede the defaulted ones, so dataclass field ordering holds. `load_config()` constructor (lines 43–50) and the `required` list (line 38) match the plan's instructions. `data.get("telegram_alerts") or []` correctly handles missing/null/empty.
- **Task 2 — `orchestrator.json.example`:** Current last key is `telegram_chat_id` (line 7). Adding `"telegram_alerts": []` after it (with the trailing comma fix) keeps valid JSON.
- **Task 3 — `notify.py`:** `send_telegram(token, chat_id, text)` exists (line 10) and is left untouched. The module already has `from __future__ import annotations`, so the `"OrchestratorConfig"` annotation resolves fine under a `TYPE_CHECKING` guard. Note: the implementer must also add `from typing import TYPE_CHECKING` (the plan implies but does not spell this out) — minor.
- **Task 4 — `main.py`:** Import on line 15 is `from .notify import send_telegram`. Both stop/rate-limit blocks are in `cli()` at lines 756–761 and 768–773, exactly as described. After conversion, `send_telegram` has no other references in `main.py`, so dropping it from the import (as the plan allows) is correct and avoids an unused import.
- **Task 5 — `main.py`:** Success-path `_git_commit(project_dir, milestone.title)` calls confirmed at lines 281 + 386 (`process_milestone`) and 523 + 629 (`process_test_milestone`). `config` is a parameter in both functions (lines 245, 489), so it is in scope. The grep found exactly these four commit calls — no skip-path `_git_commit` to confuse.
- **Task 6 — `main.py`:** `_run_dynamic_loop()` has both the pre-loop `if not pending: return` (line 645) and the in-loop `if not pending: break` (line 661). `config` and `project_dir` are parameters (line 636), so the `notify(...)` call is in scope.

## Context Gates

- **Architecture (`ARCHITECTURE.md` present):** No boundary violation. Notification logic stays in `notify.py`; `main.py` orchestrates call sites. Consistent with the file-based, single-responsibility module layout. — OK
- **Rules (`RULES.md`):** Not present. — WARN (optional file missing, non-blocking)
- **Roadmap:** Plan maps 1:1 to ROADMAP.md line 79 ("Telegram configurable alerts"). Field name, `field(default_factory=list)`, three call-site categories, and all three message formats match the milestone spec exactly. — OK
- **skill-context (`aif-review/SKILL.md`):** Not present. — WARN (no project overrides to apply)

## Observations (non-blocking)

1. **Behavioral change for existing users (by design).** With `telegram_alerts` defaulting to `[]`, an existing user who has `telegram_bot_token`/`telegram_chat_id` set but no `telegram_alerts` key will *silently stop receiving stop/rate-limit notifications* until they add `"stop"` to their config. This is the intended opt-in semantics ("replacing the always-on stop-only behavior"), and Docs are scoped out — but it is worth being aware of as a migration footgun. Consider noting it in a commit message.

2. **Example config usefulness.** `orchestrator.json.example` will ship `"telegram_alerts": []`, i.e. a copy of the example sends zero notifications. A commented/illustrative value like `["stop", "milestone", "done"]` would be more discoverable, but `[]` is valid and matches the roadmap spec — leaving as-is is acceptable.

3. **No validation of alert-type strings.** Unknown values in `telegram_alerts` simply never match and are silently ignored. Acceptable given "Logging: minimal"; no action needed.

4. **`"done"` alert fires for both modes.** `_run_dynamic_loop()` is shared by implement and test flows, so test-mode completion also sends "All milestones done". The message does not distinguish mode. This is consistent behavior and fine.

## Positive Notes

- Accurate line references and correct understanding of variable scope at every call site.
- Sensible task ordering and commit plan: Commit 1 (config + notify helper) leaves `main.py` on the old `send_telegram` path, so there is no broken intermediate state before Commit 2 wires the new call sites.
- Early-return guard order in `notify()` (alert-type check, then credentials, then send) is correct and keeps `send_telegram` unchanged.
- Correctly excludes `mark_skipped()` paths from milestone alerts and leaves the pre-loop startup check untouched.

PLAN_REVIEW_PASS
