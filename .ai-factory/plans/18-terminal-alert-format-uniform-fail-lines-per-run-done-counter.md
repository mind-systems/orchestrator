# Plan: Terminal alert format: uniform fail lines + per-run done counter

## Context
Make terminal Telegram alerts consistent: the three phase-failure raises get uniform first lines (`Plan failed` / `Implement failed` / `Test failed`), and every terminal alert reports how many milestones this run actually completed.

## Settings
- Testing: yes (spec-required unit tests for `_run_summary`)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Run-completed counter plumbing

- [x] **Task 1: Add per-run `milestones_done` counter to process state**
  Files: `orchestrator/state.py`
  Add `milestones_done: int = 0` beside `run_started` — process state only, never persisted to the sidecar (mirror the existing `run_started` module-global style). Per the spec: it answers "how much work did this run actually complete".

- [x] **Task 2: Add `_run_summary()` helper and use it at the force-quit alert**
  Files: `orchestrator/runtime.py`
  Add `def _run_summary() -> str:` returning `f"Ran for {_run_elapsed()} · {state.milestones_done} milestones done"` — the single home of this format string. `runtime.py` already imports `state`, so `state.milestones_done` is reachable. When `run_started is None`, `_run_elapsed()` already returns `"unknown"`, giving `Ran for unknown · 0 milestones done`. Then in `_handle_sigint` force-quit path (currently `notify(state.config, f"...\nRan for {_run_elapsed()}", "stop")` at line 20), replace the `Ran for {_run_elapsed()}` fragment with `{_run_summary()}`. Literal suffix is exactly ` · {n} milestones done` — no singular special-casing, no percentages.

### Phase 2: main.py wiring

- [x] **Task 3: Uniform fail first lines at the three phase-failure raises** (depends on Task 1)
  Files: `orchestrator/main.py`
  Change only the first line of each of the three phase-failure messages; keep everything after the first line (the `Last review:`/`Last run:` path + content body stays for console `STOPPED — {e}` and `/milestone-rescue`):
  - Plan-review exhaustion `PipelineStopError` (currently `f"Plan failed review after {max_iterations} attempt(s).\n\n" ...`, ~line 291): first line → `Plan failed`.
  - `IMPLEMENT_MODE.max_iterations_message` (~line 55): first line → `Implement failed` (rest `\n\nLast review: {path}\n\n{content}` unchanged).
  - `TEST_MODE.max_iterations_message` (~line 71): first line → `Test failed` (rest `\n\nLast run: {path}\n\n{content}` unchanged).
  Do NOT touch the invariant-violation raises — the "No passing plan review found…" `PipelineStopError` (~line 305), the "checkbox is still unchecked…" `PipelineStopError` (~line 394), and the "Resume at iteration … exceeds max_iterations" `HaltError` (~line 312) keep their exact wording; they are protocol violations, not phase failures.

- [x] **Task 4: Reset the counter per run and increment it on completion** (depends on Task 1)
  Files: `orchestrator/main.py`
  - In `run_implement` and `run_test`, set `state.milestones_done = 0` alongside the existing `state.run_started = time.monotonic()` assignment (top of each run).
  - Increment `state.milestones_done += 1` immediately after each `mark_done` in `process_milestone` — in BOTH completion paths: the resume-`done` early return (~line 234, before the `notify` "Milestone done") and the normal completion (~line 351, after the `mark_done`/`_git_commit`). Do NOT increment on `mark_skipped`.

- [x] **Task 5: Route every terminal alert through `_run_summary()`** (depends on Task 2, Task 4)
  Files: `orchestrator/main.py`
  Update the import: swap `_run_elapsed` for `_run_summary` in the existing `from .runtime import ...` line → `from .runtime import _handle_sigint, _run_summary, _with_caffeinate`. These five sites are `main.py`'s only references to `_run_elapsed`, so after the replacement below it must be dropped from the import (no linter is configured, but it is dead code in the milestone's own file). `_run_summary` calls `_run_elapsed` internally within `runtime.py`, so the elapsed value is still produced. Replace the `Ran for {_run_elapsed()}` fragment with `{_run_summary()}` at the five main.py terminal-alert sites:
  - all-milestones-done `done` alert in `_run_dynamic_loop` (~line 388).
  - manual-stop `stop` alert after the loop in `_run_dynamic_loop` (~line 413).
  - `PipelineStopError` handler `milestone-fail` alert in `cli()` (~line 497).
  - `HaltError` handler `stop` alert in `cli()` (~line 504).
  - generic-`Exception` handler `stop` alert in `cli()` (~line 509).
  Leave the per-milestone green `milestone` alerts untouched (a counter there is meaningless). Do not change alert types, emoji, or the `cli()` `splitlines()[0]` first-line extraction. The console `>>> Ran for …` prints in `runtime.py` use `runtime`'s own module-level `_run_elapsed` and are unaffected by the `main.py` import change.

### Phase 3: Tests

- [x] **Task 6: Unit-test `_run_summary` formatting** (depends on Task 2)
  Files: `tests/test_main.py` (or a small new `tests/test_runtime.py`)
  Import `orchestrator.state` and `orchestrator.runtime`. Pin the two silent-failure cases from the spec: (a) with `state.run_started` set and `state.milestones_done = N` → `Ran for … · N milestones done` (assert the ` · {N} milestones done` suffix); (b) `state.run_started = None`, `state.milestones_done = 0` → exactly `Ran for unknown · 0 milestones done`. Restore/save-and-reset `state.run_started` and `state.milestones_done` around the test so module-global mutation doesn't leak into other tests (use a fixture or try/finally). Run `uv run pytest` — green.

## Commit Plan
- **Commit 1** (after tasks 1-2): "Add per-run milestones-done counter and run-summary helper"
- **Commit 2** (after tasks 3-5): "Uniform terminal fail lines and per-run done counter in alerts"
- **Commit 3** (after task 6): "Test run-summary formatting"
