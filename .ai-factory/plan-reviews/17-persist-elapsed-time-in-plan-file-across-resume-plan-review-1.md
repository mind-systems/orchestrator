# Plan Review: 17-persist-elapsed-time-in-plan-file-across-resume

## Summary
The plan correctly diagnoses the bug, picks a low-risk storage mechanism (an extra key inside the existing `<!-- orchestrator-sessions -->` block), and identifies the right insertion points in `process_milestone` and `process_test_milestone`. The bias-on-resume + checkpoint-after-each-step pattern is sound and the cited line numbers all match the current `orchestrator/main.py`.

Verified prerequisites:
- `_write_session` (`agents.py:43`) is genuinely key-agnostic — it treats `role` as an arbitrary key and the early-return on `not session_id` is fine because `str(int(...))` is `"0"` or larger and always truthy.
- `_read_sessions` (`agents.py:28`) returns `{}` on missing file or missing block, so `sessions.get("elapsed", "0")` is safe for milestones planned before this change.
- All `~line N` references in the plan match `main.py` exactly (150, 157, 169–172, 188, 196, 229, 234, 248, 536, 543, 555–558, 569–572, 574, 582, 613, 618, 635).
- `mark_done()` (`roadmap.py:67`) already takes `elapsed_secs: int | None` — no signature change needed.

## Critical Issues

### 1. `process_refactor_milestone` is not covered by the plan
The plan addresses `process_milestone` (Phase 1) and `process_test_milestone` (Phase 2), but `process_refactor_milestone` (`main.py:256–376`) has the identical bug:
- Line 275: `milestone_start = time.monotonic()` — resets on every resume.
- Line 282–288: `step == "done"` branch reports an under-counted `elapsed`.
- Line 371: final `elapsed = int(time.monotonic() - milestone_start)` passed to `mark_done()` and printed.

Since `run_refactor` is one of the three primary entry points (`uv run orchestrator refactor`) and uses the same `_detect_milestone_step` resume path as `process_milestone`, leaving it untouched means a refactor milestone resumed across restarts will still report incorrect elapsed time in `ROADMAP.md`. This is exactly the bug the plan claims to fix.

Recommended fix: add a Phase 3 with two tasks mirroring Phase 1 — read offset and bias `milestone_start` after `_detect_milestone_step` (around line 276), and checkpoint after `step = "plan_review"` (line 308), after `plan_passed = ...` (line 316), after `implementer.implement(...)` (line 349), and after `passed = refactor_planner.verify(...)` (line 355).

## Minor Issues

### 2. Pre-existing `milestone_start = time.monotonic()` becomes dead code
Lines 150, 275, and 536 are immediately overwritten by the new `milestone_start = time.monotonic() - elapsed_offset` assignment. The plan doesn't say to remove them, so they stay as a tiny inconsistency (one extra `time.monotonic()` call) but are harmless. Consider removing them for clarity, or explicitly leaving them with a comment that the bias path re-initializes.

### 3. `_write_session` name becomes a slight misnomer
With an `elapsed` key alongside `planner` / `implementer`, the helper is no longer storing only session IDs. Not a functional issue (the plan explicitly leans on its key-agnosticism), and renaming would expand scope unnecessarily — flagging only as a future cleanup signal.

### 4. Document the on-disk schema bump
The `<!-- orchestrator-sessions -->` block grows a new well-known key. A one-line comment in `_read_sessions` / `_write_session` describing the recognized keys (`planner`, `implementer`, `elapsed`) would help future readers. Optional; not blocking.

## Positive Notes
- Reusing the existing comment block avoids any new parsing infrastructure or migration step — old plan files seamlessly default to `elapsed=0`.
- Checkpointing after each completed step (rather than only at the end) means accumulated time is preserved even if the process is killed mid-iteration.
- Plan correctly handles the skipped-milestone early-return path by guarding writes on `plan_path.exists()` (and `_write_session` itself also guards on this — defense in depth).
- Reusing the `sessions` dict already read for the bias to set `planner`/`implementer` session IDs avoids a redundant file read and is a nice tidy-up.
- The done-branch behaviour is correct without any additional changes because the bias is applied before `if step == "done":` is evaluated.

## Verdict
The plan is correct and well-targeted for the two pipelines it covers, but it leaves the `refactor` pipeline with the same bug. Add Phase 3 for `process_refactor_milestone`, then this is ready to implement.
