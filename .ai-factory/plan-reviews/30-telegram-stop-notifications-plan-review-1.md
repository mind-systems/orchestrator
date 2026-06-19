# Plan Review: Telegram stop notifications

**Plan:** `.ai-factory/plans/30-telegram-stop-notifications.md`
**Files Reviewed:** 4 (config.py, main.py, orchestrator.json.example, agents.py)
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture** (`.ai-factory/ARCHITECTURE.md`): WARN-free. Project is "Layered, ~5 modules". Adding a single stdlib-only `notify.py` peer module is consistent with the existing flat module layout (`agents.py`, `config.py`, `main.py`, `roadmap.py`, `state.py`). No boundary or dependency violations.
- **Rules** (`.ai-factory/RULES.md`): Not present — no explicit rule set to enforce.
- **Roadmap** (`.ai-factory/ROADMAP.md`): Linked. Milestone "Telegram stop notifications" (line 77) describes this work in detail and the plan matches it faithfully (config fields not in `required`, stdlib `urllib`, try/except, truthiness guard, first-line-only message). Good alignment.

## Verification Against Codebase

All plan assumptions check out:
- `OrchestratorConfig` dataclass (config.py:11-16) ends with `enable_phase_sessions` — the two new optional fields slot in after it cleanly. Existing fields are all required (no defaults), so appending fields *with* defaults is valid Python (no non-default-after-default error).
- `load_config()` `required` list (config.py:36) correctly excludes the new keys per the plan; `data.get(...) or None` coercion is sound and matches the existing construction style.
- `orchestrator.json.example` (verified) currently ends at `"enable_phase_sessions": false` with no trailing comma — the plan's instruction to add a comma + two keys keeps valid JSON.
- `PipelineStopError` and `RateLimitError` both exist (agents.py:52-57) and `RateLimitError` is raised from `_run_claude` (agents.py:183, 198), propagating up through `_with_caffeinate` → `run_implement`/`run_test` → into `cli()`'s existing `except` blocks. The wiring point is real.
- In `cli()` (main.py:741-759), both `config` and `project_dir` are in scope at both catch points, exactly as the plan states. The print-then-notify-then-`sys.exit(0)` insertion point is correct.
- `urllib.request.urlopen(url, data=payload, ...)` with a non-None `data` correctly issues a POST; `urlencode(...).encode()` body is the right format for Telegram's `sendMessage`. Stdlib-only, no new deps — confirmed.

## Minor Suggestions (non-blocking)

1. **Empty exception message edge case.** `str(e).splitlines()[0]` raises `IndexError` when the exception message is empty — verified `"".splitlines() == []`. `RateLimitError(result_text)` is constructed from CLI output (agents.py:183/198) which could theoretically be empty, and this `msg` computation sits *outside* `send_telegram`'s try/except, so it would turn a clean `sys.exit(0)` into a traceback. Cheap hardening: `msg = (str(e).splitlines() or [""])[0]`. Worth folding into Task 4.

2. **HTTP response handling (informational).** `urlopen` returns a response object that is not read/closed in the plan. For a fire-and-forget notification this is acceptable; the surrounding `try/except` already absorbs failures. No change required.

## Positive Notes

- Scope is tight and correct: optional credentials, silent no-op when absent, no new dependencies, first-line-only message to avoid dumping full review text into Telegram.
- Task ordering and dependencies are accurate (Task 4 depends on Task 1 + Task 3).
- The truthiness guard (`config.telegram_bot_token and config.telegram_chat_id`) combined with `or None` coercion correctly handles the empty-string-in-config case.

The plan is complete, accurate against the codebase, and safe to implement. The single edge case above is trivial hardening the implementer can apply inline.

PLAN_REVIEW_PASS
