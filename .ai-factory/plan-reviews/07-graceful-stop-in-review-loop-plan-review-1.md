## Plan Review: Graceful stop in review loop

**Plan:** `.ai-factory/plans/07-graceful-stop-in-review-loop.md`
**Files affected:** `orchestrator/main.py`
**Risk Level:** Low

### Verification

All line-number references in the plan match the current codebase:

- `_handle_sigint` ends at line 40, `_next_number` starts at line 43 — placement "around line 42" is correct.
- `_implement_loop` loop at lines 327-331 — matches. Has the `state.stop_requested` guard.
- `_refactor_loop` loop at lines 354-358 — matches. Has the `state.stop_requested` guard.
- `run_review` inner `loop()` at lines 442-444 — matches. Correctly identified as missing the stop guard.
- `run_implement_review` inner `loop()` at line 383 — matches. No stop gate between implement and review phases.

The `state` module (single `stop_requested: bool = False` global) is correctly referenced throughout.

### Analysis

**Task 1 (`_run_loop` helper):** Clean abstraction. The signature `_run_loop(items, process_fn)` is generic enough to handle both `enumerate(pending, start=N)` (tuples) and plain list iteration (single items). Placement after `_handle_sigint` is logical.

**Task 2 (replace loops):** All three replacement sites are correctly identified. The existing `_implement_loop` and `_refactor_loop` each have a 4-line stop-check block that collapses into a single `_run_loop` call. The `run_review` inner `loop()` gains a stop check it currently lacks — this is the primary bug being fixed.

**Task 3 (implement→review gate):** Correct placement — after `_implement_loop` returns, before the review-file cleanup and `run_review` call. If the user Ctrl+C'd during implement, skipping the cleanup is the right behavior: the implement-phase review files stay intact for inspection, and a subsequent `implement-review` run will handle them normally.

### Positive Notes

- Focused scope — three tasks, one file, one concern.
- The `_run_loop` helper eliminates three separate stop-check patterns in favor of one, which reduces future drift.
- The plan correctly leaves the inner iteration loops (inside `process_milestone`, `process_refactor_milestone`, `review_plan`) untouched — those run within a single milestone, and the SIGINT handler's message ("will stop after the current milestone finishes") confirms that between-iteration stopping is intentionally not supported.

PLAN_REVIEW_PASS
