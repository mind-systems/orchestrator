# Plan Review: 16-persist-agent-session-ids-in-plan-file

## Summary

The plan is concrete, scoped, and aligns with the design captured in `.ai-factory/notes/03-session-id-persistence.md`. File paths, line numbers, function names, and call sites all match the current code. Edge cases (plan_path missing, empty session_id, missing block, role appending) are handled by the helper implementations referenced. The plan-review/restore ordering is correct: restoration happens after `_detect_milestone_step()` canonicalizes `plan_path` and before the `if step == "plan":` block, so a counter>1 plan revision can resume the planner's prior session.

## Verification against the codebase

- `orchestrator/agents.py:21–22` — `MAX_RETRIES`/`RETRY_DELAY` are the module-level constants; helpers are correctly placed after them. ✓
- `orchestrator/agents.py:205` — `_run_claude(...)` call in `PlannerReviewer.plan()` assigns `self.session_id`; `plan_path` is in scope (param). ✓
- `orchestrator/agents.py:227` — `_run_claude(...)` call in `PlannerReviewer.review()` assigns `self.session_id`; `plan_path` is in scope. ✓
- `orchestrator/agents.py:343` — `_run_claude(...)` call in `Implementer.implement()` assigns `self.session_id`; `plan_path` is in scope. ✓
- `orchestrator/main.py:13` — current import line matches Task 4's expected before/after. ✓
- `orchestrator/main.py:151` — `_detect_milestone_step()` returns canonical `plan_path`; `process_milestone()` restore block correctly runs after line 167 (`implementer = Implementer(project_dir)`) and before line 170 (`if step == "plan":`). ✓
- `orchestrator/main.py:548` — `process_test_milestone()` builds `planner_reviewer`, `implementer`, `test_runner`, then enters `if step == "plan":` at line 551. Restore block fits between them, matching the `process_milestone()` pattern. ✓
- `_detect_milestone_step()` returns `("plan", 1, plan_path)` when `plan_path` doesn't exist (line 95), so the `if plan_path.exists():` guard correctly skips restoration for first-time plans. ✓

## Observations (non-blocking)

1. **Refactor mode writes implementer sessions but never reads them.** `Implementer.implement()` is shared with `process_refactor_milestone()`, so the new `_write_session(plan_path, "implementer", ...)` will also fire there. The plan explicitly excludes refactor restoration. Result: refactor flow's plan files will accumulate a sessions block that's never used. This is harmless (dead data, not a bug) and consistent with the scope note in `notes/03`. If you want strict cleanliness later, gate the write — but doing so would require threading a flag into the agent, which isn't worth it.

2. **Planner-revision overwrites may discard the sessions block.** When `PlannerReviewer.plan(..., plan_review_path=...)` revises an existing plan, the Claude agent will typically `Write` the new plan file, which would erase the trailing HTML comment block. `_write_session` runs immediately after and re-adds the `planner:` line, so steady state is correct. There can't be a stale `implementer:` line at that point because plan revision only happens while step is in `("plan", "plan_review")`, i.e. before implementation. No action needed; calling this out so the implementer doesn't try to "preserve" the block by editing the planner prompt.

3. **`re` import placement.** Task 1's wording ("after the existing import block, before `from pathlib import Path` if needed") is slightly ambiguous. Standard PEP 8 placement is alphabetical within the stdlib `import X` group — between `os` and `subprocess`. Either spot works; the implementer should just keep the group alphabetical.

4. **Roles are hardcoded literals.** `"planner"` and `"implementer"` strings appear in three call sites in `agents.py` and two in `main.py`. Acceptable for a two-role design, but typos would silently produce dead writes / no restoration. Consider a small `_SESSION_ROLES = ("planner", "implementer")` tuple or named constants if you want one source of truth — purely a stylistic suggestion, not required.

5. **Session ID can change on resume.** `_run_claude` always re-assigns `self.session_id` from the JSON output, even on `--resume`. The plan correctly persists after every call (not just on first creation), which keeps the stored ID current. ✓

## Missing steps / wrong assumptions

None identified. The plan correctly:
- Reuses helpers verbatim from `notes/03` (no drift between design doc and tasks).
- Places restore *before* the plan step so revision iterations re-use the planner session.
- Skips `PlannerReviewer.patch()` (correctly noted as unused in implement/test flows where this matters).
- Skips `process_refactor_milestone()` restoration (per design scope).
- Imports `_read_sessions` (not `_write_session`) in `main.py`, since writes only happen inside agent methods.

## Security / migration / API concerns

- HTML-comment block at end of `.md` file is invisible to markdown renderers and ignored by all agents reading the plan. No leakage risk beyond the existing `.ai-factory/plans/` directory.
- No CLI/API surface changes.
- No external migration required; the helpers gracefully handle plans without the sessions block (returns `{}`).
- Concurrency: orchestrator processes one milestone at a time, so no race on plan file writes.

PLAN_REVIEW_PASS
