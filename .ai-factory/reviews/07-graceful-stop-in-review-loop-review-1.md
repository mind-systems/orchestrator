## Code Review: Graceful stop in review loop

**Plan:** `.ai-factory/plans/07-graceful-stop-in-review-loop.md`
**Files changed:** `orchestrator/main.py`

### Verification

All three tasks from the plan are implemented correctly:

1. **`_run_loop` helper** (lines 43-49): Iterates items, checks `state.stop_requested` before each, prints halt message and returns. Clean and minimal.

2. **Loop replacements** — all three call sites converted:
   - `_implement_loop` (lines 336-339): `enumerate` tuples unpacked via `item[0]`/`item[1]` — argument order to `process_milestone(project_dir, milestone, i, max_iterations)` is preserved correctly.
   - `_refactor_loop` (lines 362-365): Same pattern, same correct argument mapping.
   - `run_review` inner `loop()` (line 454): Gains a stop check it previously lacked — this was the primary bug.

3. **Implement→review gate** (lines 393-395): Inserted after `_implement_loop` returns, before review-file cleanup and `run_review`. Ctrl+C during implement now prevents the review phase.

### Analysis

- **`enumerate` as iterator**: `_run_loop` accepts any iterable; `enumerate(...)` works fine.
- **Lambda binding**: The lambdas capture `project_dir` and `max_iterations` from enclosing scope (function parameters, immutable during iteration). `item` is the lambda's own parameter. No late-binding issues.
- **SIGINT safety**: `state.stop_requested` is a module-level bool. Python's GIL makes the write from the signal handler and the read in `_run_loop` effectively atomic. Unchanged from the original design.
- **Message text change**: Original loops used `"halting before next milestone."` — now uses `"halting."` from the shared helper. Consistent with the milestone spec and appropriate since `_run_loop` also handles plan review items (not milestones).
- **No behavior regression**: The `_run_loop` check happens at the same point (before each item) as the original hand-written guards. The `run_review` loop gains protection it didn't have before.

No bugs, no security issues, no correctness problems found.

REVIEW_PASS
