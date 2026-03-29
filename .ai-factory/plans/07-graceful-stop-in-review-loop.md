# Plan: Graceful stop in review loop

## Context
The review loop inside `run_review` does not check `state.stop_requested`, so Ctrl+C during a review pass doesn't stop between plans. Extract a shared `_run_loop` helper that checks `stop_requested` before each item, and use it in all three iteration sites. Also guard the implement-to-review transition in `run_implement_review`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Shared helper

- [x] **Task 1: Add `_run_loop` helper function**
  Files: `orchestrator/main.py`
  Add a module-level function `_run_loop(items, process_fn)` near the other `_`-prefixed helpers (after `_handle_sigint`, around line 42). It iterates over `items`, checks `state.stop_requested` before each item — if set, prints `>>> Stop requested — halting.` and returns early. Otherwise calls `process_fn(item)`. This is the single place where the stop-check-and-halt logic lives.

### Phase 2: Replace existing loops

- [x] **Task 2: Replace `for` loops in `_implement_loop`, `_refactor_loop`, and `run_review`** (depends on Task 1)
  Files: `orchestrator/main.py`
  **`_implement_loop`** (line 327-331): Replace the `for i, milestone in enumerate(...)` block (including the `if state.stop_requested` guard) with a single `_run_loop` call. Pass `enumerate(pending, start=_next_number(plans_dir))` as items. The `process_fn` receives each `(i, milestone)` tuple and calls `process_milestone(project_dir, milestone, i, max_iterations)`.
  **`_refactor_loop`** (line 354-358): Same pattern — replace the `for` + guard with `_run_loop`. The `process_fn` calls `process_refactor_milestone(project_dir, milestone, i, max_iterations)`.
  **`run_review` inner `loop()`** (line 442-444): Replace the bare `for plan_path in pending` (which currently has no stop check) with `_run_loop(pending, ...)`. The `process_fn` receives each `plan_path` and calls `review_plan(project_dir, plan_path, max_iterations)`.

- [x] **Task 3: Add stop check between implement and review in `run_implement_review`** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `run_implement_review`'s inner `loop()` function (line 383), add a `state.stop_requested` check after `_implement_loop` returns and before the review cleanup/`run_review` call. If `state.stop_requested` is true, print `>>> Stop requested — halting.` and return early — so that Ctrl+C during the implement phase prevents the review phase from starting.
