# Plan: Total run time in terminal Telegram alerts

## Context
Every terminal Telegram alert (all-milestones-done, `PipelineStopError`, `RateLimitError`) gains a final `Ran for <elapsed>` line so total wall-clock run time survives in the one durable channel, since console totals are ephemeral and rolled-back milestones lose their sidecar `elapsed`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Run-start timestamp

- [x] **Task 1: Add `run_started` to `state.py`**
  Files: `orchestrator/state.py`
  Add a module-level `run_started: float | None = None` alongside `stop_requested` / `active_proc`. This is the shared home for the run-start monotonic timestamp, reachable from both the loop (done alert in `main.py`) and the `cli()` exception handlers (stop alerts). Follow the existing typed module-global style already in the file. No other changes.

### Phase 2: Timestamp set + elapsed helper

- [x] **Task 2: Stamp the start and add the `_run_elapsed()` helper** (depends on Task 1)
  Files: `orchestrator/main.py`
  - In `run_implement()` (`main.py:736`) and `run_test()` (`main.py:745`), add `state.run_started = time.monotonic()` as the **first statement** of each function, before `signal.signal(...)` / `_with_caffeinate(...)`. (`state` and `time` are already imported; `_with_caffeinate`'s own local `start` and its console prints stay untouched.)
  - Add a helper near `_fmt_elapsed` (`main.py:406`):
    ```python
    def _run_elapsed() -> str:
        if state.run_started is None:
            return "unknown"
        return _fmt_elapsed(int(time.monotonic() - state.run_started))
    ```
    The `None` guard is defensive — notify sites must never crash on a missing timestamp. Reuse the existing `_fmt_elapsed` formatting; do not duplicate it.

### Phase 3: Append elapsed to terminal alerts

- [x] **Task 3: Append `Ran for <elapsed>` to the three terminal alerts** (depends on Task 2)
  Files: `orchestrator/main.py`
  Add `\nRan for {_run_elapsed()}` as the final line of each terminal `notify(...)` message:
  - All-milestones-done in `_run_dynamic_loop` (`main.py:685`): `notify(config, f"All milestones done: {project_dir.name}\nRan for {_run_elapsed()}", "done")`.
  - `PipelineStopError` handler in `cli()` (`main.py:780`): append `\nRan for {_run_elapsed()}` after the existing first-line excerpt (`{msg}`).
  - `RateLimitError` handler in `cli()` (`main.py:787`): same append.
  Leave the four `milestone` notify calls (`main.py:287,399,547,652`) and the alert `type` strings (`"done"`/`"stop"`) unchanged. Do not add new alert types or config keys. The early-return "All milestones are done!" startup path (`main.py:669`) sends no alert and stays as-is.

## Notes
- `state.py` is the cross-layer global-flag module (per `ARCHITECTURE.md` dependency rules: importable from any layer), so it is the correct home for `run_started` — no dependency-direction violation.
- Single commit at the end: "Append total run time to terminal Telegram alerts".
