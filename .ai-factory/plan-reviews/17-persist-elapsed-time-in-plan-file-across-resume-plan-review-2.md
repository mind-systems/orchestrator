# Plan Review: 17-persist-elapsed-time-in-plan-file-across-resume (v2)

## Summary
This iteration addresses the v1 blocker by adding Phase 3 for `process_refactor_milestone`. All three milestone pipelines are now covered. The bias-on-resume + checkpoint-after-each-step pattern remains sound, line numbers all match the current `orchestrator/main.py`, and the underlying helpers (`_read_sessions`, `_write_session`) are confirmed key-agnostic.

Verification against current code:
- `_write_session` (`agents.py:43`) — key-agnostic; early-return on `not session_id` is fine because `str(int(...))` is `"0"` or larger and always truthy.
- `_read_sessions` (`agents.py:28`) — returns `{}` on missing file or missing block, so `sessions.get("elapsed", "0")` is safe for pre-existing plans.
- All cited line numbers verified:
  - Phase 1: 150, 157, 169–172, 184–186, 188, 192–212, 229, 234, 248. ✓
  - Phase 2: 536–558, 543, 555–558, 569–572, 574, 578–598, 613, 618, 635. ✓
  - Phase 3: 275, 282, 290–292, 303–306, 308, 312–332, 316, 349, 355, 371. ✓
- `_detect_milestone_step` is reused by `process_refactor_milestone` (line 276) — confirms the same resume-path bug exists and the same fix applies.
- The skipped-milestone early-return guards (`mark_skipped(...)`; `return`) in all three functions occur **before** the new `step = "plan_review"` checkpoint write, so the `plan_path.exists()` guard on those writes is defense-in-depth (also handled by `_write_session` itself) — harmless redundancy.

## Critical Issues
None.

## Minor Issues

### 1. Unspecified default for `sessions` / `elapsed_offset` when `plan_path.exists()` is false
Tasks 1, 3, and 5 say "check whether `plan_path.exists()` and if so call `_read_sessions(plan_path)`" and then "reassign `milestone_start = time.monotonic() - elapsed_offset`". The assignment to `milestone_start` happens unconditionally (it must, to cover the `step == "done"` branch later), but the plan does not explicitly state that `elapsed_offset = 0` (or `sessions = {}`) must be set in the `not plan_path.exists()` branch. Implementer must infer this. Suggest making it explicit, e.g. `sessions = _read_sessions(plan_path) if plan_path.exists() else {}` followed by an unconditional `elapsed_offset = int(sessions.get("elapsed", "0"))` and unconditional `milestone_start = time.monotonic() - elapsed_offset`. Not blocking — a careful implementer will arrive at this naturally — but explicit is better.

### 2. Phase 3 lacks the `_write_session` import note that Phase 1 carries
Task 1 says "Import `_write_session` alongside the existing `_read_sessions` import on line 13". Tasks 3 and 5 don't repeat this, but since Task 1 has the import as a hard dependency for Tasks 2/4/6, this is implicit. Worth a single line note in Task 5 (`process_refactor_milestone` does not currently use `_read_sessions` at all — it's a brand-new symbol in this function's scope) so the implementer doesn't think the line-13 import is `process_milestone`-local. Trivial nit.

### 3. Pre-existing `milestone_start = time.monotonic()` lines are correctly removed
This was a minor item in v1. The v2 plan explicitly says "Drop the original `milestone_start = time.monotonic()` at line 150" / "line 275" / "line 536" in Tasks 1, 3, and 5 respectively. Resolved.

## Positive Notes
- Phase 3 now closes the gap identified in v1 — `uv run orchestrator refactor` will report correct cumulative time across restarts.
- The plan correctly notes that `process_refactor_milestone` does not currently restore session IDs from the plan file and explicitly marks that as out of scope, preventing accidental scope creep.
- Reusing the already-read `sessions` dict for both `elapsed_offset` and the existing `planner`/`implementer` session-id restoration (Tasks 1 and 3) avoids a redundant file read — clean refactor.
- Checkpointing after every completed step (plan, each plan-review attempt, each implement, each review/test/verify) means accumulated time survives a kill at any granularity — the worst case loses only the in-flight step.
- The `step == "done"` early-return branch in all three functions now works correctly with zero additional changes, because the bias is applied before that conditional is evaluated.
- The `<!-- orchestrator-sessions -->` block schema extension is backward-compatible: existing plans without an `elapsed` key default to `0`, so the change is safe for milestones already in flight.

## Verdict
The plan is correct, complete, and well-targeted. All three milestone pipelines are now covered with consistent treatment. Minor wording suggestions above are non-blocking. Ready to implement.

PLAN_REVIEW_PASS
