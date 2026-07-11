## Code Review: Terminal alert format — uniform fail lines + per-run done counter

**Plan:** `.ai-factory/plans/18-terminal-alert-format-uniform-fail-lines-per-run-done-counter.md`
**Spec:** `.ai-factory/specs/15-terminal-alert-format.md`
**Files changed:** `orchestrator/state.py`, `orchestrator/runtime.py`, `orchestrator/main.py`, `tests/test_runtime.py`

### Scope
Reviewed the full diff (`git diff HEAD`) and read each changed file in full for surrounding context. The change is a faithful, complete implementation of the plan.

### Verified correct (ground-truth)

- **State (`state.py`):** `milestones_done: int = 0` added as a module global beside `run_started` — process state, not persisted to the sidecar. Matches the plan and the `run_started` idiom.
- **`_run_summary` (`runtime.py:38-39`):** Returns `f"Ran for {_run_elapsed()} · {state.milestones_done} milestones done"` — the single home of the format. `runtime.py` imports `state` at module level (line 10), so `state.milestones_done` is reachable. No circular-import risk (`state.py` only TYPE_CHECKING-imports config). When `run_started is None`, `_run_elapsed()` returns `"unknown"`, yielding exactly `Ran for unknown · 0 milestones done`.
- **Uniform fail lines (`main.py`):** All three phase-failure first lines unified — `IMPLEMENT_MODE.max_iterations_message` → `Implement failed`, `TEST_MODE.max_iterations_message` → `Test failed`, plan-review exhaustion `PipelineStopError` → `Plan failed`. The `\n\nLast review/run: {path}\n\n{content}` bodies are preserved for the console `STOPPED —` block and `/milestone-rescue`. Removing `{n}` from the two templates is safe: the `.format(n=max_iterations, path=…, content=…)` call at the raise site keeps passing `n=`, which `str.format` silently ignores — no `KeyError`, no crash.
- **Invariant raises untouched:** no-passing-plan-review `PipelineStopError`, unchecked-checkbox guard, and resume-exceeds-max `HaltError` retain their exact wording — correctly excluded as protocol violations, not phase failures.
- **Counter reset (`main.py`):** `state.milestones_done = 0` set in both `run_implement` and `run_test` beside `state.run_started = time.monotonic()`. Per-run semantics: restarts at 0 after interrupt + rerun.
- **Counter increment (`main.py`):** `state.milestones_done += 1` after `mark_done` in both completion paths — the resume-`done` early return and the normal completion. `mark_skipped` is not counted. Correct per spec ("how much work did this run actually complete").
- **Terminal-alert sites:** All six replaced with `_run_summary()` — five in `main.py` (all-milestones-done `done`, manual-stop `stop`, `PipelineStopError`, `HaltError`, generic-`Exception`) and force-quit in `runtime.py:20`. Per-milestone green `milestone` alerts left untouched. Alert types, emoji, and `cli()`'s `splitlines()[0]` extraction unchanged.
- **Dead import removed:** `_run_elapsed` swapped for `_run_summary` in `main.py`'s `from .runtime import …`. Grep confirms zero remaining `_run_elapsed` references in `main.py`. The two surviving `Ran for` strings in `runtime.py` (lines 53, 61) are the caffeinate wrapper's `>>> Ran for … before stopping.` **console** prints — not terminal Telegram alerts, correctly out of scope.
- **Tests (`tests/test_runtime.py`):** Both spec-required cases pinned — the ` · 3 milestones done` suffix for the `run_started`-set case (avoids asserting the nondeterministic elapsed portion) and the exact `Ran for unknown · 0 milestones done` for the `None` case. Both save/restore the two module globals in `finally`, preventing leakage into other tests.

### Test run
`uv run pytest` → **118 passed**.

### Findings
None. The implementation matches the plan and spec exactly, introduces no runtime errors, and the full suite is green.

REVIEW_PASS
