# Code Review: 17-persist-elapsed-time-in-plan-file-across-resume

## Summary
The implementation faithfully realizes the plan across all three milestone pipelines (`process_milestone`, `process_test_milestone`, `process_refactor_milestone`). The bias-on-resume + per-step checkpoint pattern is wired in correctly, line numbers in the plan match what landed, and the underlying helpers (`_read_sessions`, `_write_session`) already supported the new `elapsed` key with no schema change.

## Files Reviewed
- `orchestrator/main.py` — three pipelines modified plus import line
- `orchestrator/agents.py` — read-only verification of `_read_sessions` / `_write_session` semantics
- `orchestrator/roadmap.py` — read-only (no signature change; not touched)
- `.ai-factory/ROADMAP.md` — milestone description added (no functional impact)

## Verification

### Helper semantics (agents.py)
- `_write_session` (line 43) is key-agnostic; it updates an existing line with the same prefix or appends a new one, and creates the comment block if absent.
- The early-return guard `not session_id` is safe for the new caller: `str(int(time.monotonic() - milestone_start))` is `"0"` (truthy) or larger, never empty.
- `_write_session` also self-guards on `plan_path.exists()`, providing defense-in-depth for the post-`step = "plan_review"` checkpoint writes (which the pipeline code additionally gates by the early-return on a missing plan).
- `_read_sessions` returns `{}` on a missing file or missing comment block, so `sessions.get("elapsed", "0")` is correct for plans created before this change.

### process_milestone (lines 150–262)
- Original `milestone_start = time.monotonic()` removed; new block at 153–158 reads `sessions`, computes `elapsed_offset`, and unconditionally assigns `milestone_start = time.monotonic() - elapsed_offset`.
- `if step == "done":` at line 163 now correctly reports cumulative elapsed via the biased `milestone_start`.
- The `sessions: dict[str, str] = {}` annotation hoists `sessions` into the function-level scope, replacing the previous `if plan_path.exists(): sessions = _read_sessions(...)` block. The substitution `if sessions:` at line 175 is functionally equivalent to the previous `if plan_path.exists():` gate: an empty `sessions` dict can occur if either the plan file is missing **or** the file exists but has no `<!-- orchestrator-sessions -->` block, and in both cases the old code would have assigned `None` to `planner_reviewer.session_id` / `implementer.session_id` (via `dict.get`), matching the default values set in the agent constructors. No behavior change.
- Checkpoint writes are placed at all four points specified in the plan:
  - Line 194 — after `step = "plan_review"` (post-plan-creation; `plan_path.exists()` already guaranteed by the early-return at 188).
  - Line 203 — after `plan_passed = plan_reviewer.review_plan(...)`, covering both pass and revise branches.
  - Line 237 — after `implementer.implement(...)`.
  - Line 243 — after `passed = planner_reviewer.review(...)`.

### process_refactor_milestone (lines 265–391)
- Same pattern applied. `_read_sessions` is now called here for the first time (only for the `elapsed` value); session IDs intentionally not restored, matching the plan's explicit out-of-scope note.
- Checkpoint writes at lines 322, 331, 365, 372 match the four specified locations.

### process_test_milestone (lines ~536–658)
- Same pattern as `process_milestone`. Checkpoints at 597, 606, 638, 644.
- `sessions: dict[str, str] = {}` hoisting and `if sessions:` gate match the pattern; functionally equivalent to before.

## Correctness Considerations

### No critical issues
- `int(sessions.get("elapsed", "0"))` could in principle raise `ValueError` if the on-disk value were corrupted, but `_write_session` is the only writer and always stores a valid integer string. Consistent with the existing handling style in this codebase (e.g. no defensive parsing of the `planner` / `implementer` session IDs).
- `_write_session` is called with `plan_path` that may not exist only in theory: every checkpoint site is either preceded by an explicit early-return on missing plan (post-`step = "plan_review"`), or runs inside the implement/review/verify loops which are gated by the "passing plan review" safety guard — which requires the plan file to exist. The helper's own `not plan_path.exists()` guard makes this doubly safe.
- The done-branch (`if step == "done":`) correctly uses the biased `milestone_start`, so resume-into-done reports cumulative elapsed.

### Minor observations (non-blocking)
1. **Revise time isn't checkpointed separately.** When a plan-review fails and the planner re-runs at lines 215–219 / 343–347 / 618–622, the revise call's elapsed time is captured only on the next iteration's `plan_passed = ...` checkpoint. If the process is killed during the revise call, that revise time is lost on resume. The plan's spec ("checkpoint after each plan-review attempt") is followed exactly, so this is by design — flagging only.
2. **Type annotation `sessions: dict[str, str] = {}` is duplicated** in `process_milestone` and `process_test_milestone`; `process_refactor_milestone` omits it (correct — no session restoration there). Cosmetic.
3. **Multiple checkpoint writes per loop iteration are O(N) file rewrites.** Each `_write_session` reads and rewrites the plan file. For long milestones with many iterations this is dozens of small writes — fine in practice, and matches the existing per-call session ID writes already happening inside `agents.py`. Not a concern.

## Positive Notes
- Cleanly removes redundant `_read_sessions` calls in `process_milestone` and `process_test_milestone` by reusing the already-read `sessions` dict.
- All three pipelines treated consistently — same idiom, same checkpoint sites, easy to maintain.
- The schema extension (`elapsed` key in `<!-- orchestrator-sessions -->`) is backward-compatible: old plan files default to `0` via `sessions.get("elapsed", "0")`.
- Bias is applied before the `step == "done":` branch, so resume-into-done reports the full cumulative time without any additional code.
- `_write_session(plan_path, "elapsed", ...)` writes survive being called when the plan file lacks the comment block (helper creates it) and when called repeatedly (helper updates the existing `elapsed:` line in place).

REVIEW_PASS
