# Total run time in terminal Telegram alerts

**Date:** 2026-07-05
**Source:** conversation context

## Key Findings

- Telegram alerts are the only durable record of total orchestrator run time. Console prints exist (`IMPLEMENT DONE — <time>` at `main.py:741`, `>>> Ran for <time> before stopping.` at `main.py:423,431`) but scrollback is ephemeral. Per-milestone times in the roadmap survive git history, but when a failed milestone is rolled back and re-decomposed into new tasks (the `milestone-rescue` flow), its sidecar and artifacts are deleted — the burned time vanishes everywhere except a sent Telegram message.
- Requirement: every **terminal** alert carries the total wall-clock time the orchestrator process ran — all three terminal outcomes: `PipelineStopError` (max iterations / pipeline stop), `RateLimitError`, and all-milestones-done. **Milestone alerts stay unchanged** — per-milestone time is already durable in the roadmap line and recoverable from git history.

## Details

- **`state.py`:** add a module-level `run_started: float | None = None` alongside `stop_requested` — the run-start timestamp home reachable from both the loop (done alert) and the `cli()` exception handlers (stop alerts).
- **`main.py` — `run_implement()` and `run_test()`:** set `state.run_started = time.monotonic()` as the first statement (before `_with_caffeinate`). `_with_caffeinate`'s own local `start` and its console prints stay as-is.
- **Helper:** `def _run_elapsed() -> str` returning `_fmt_elapsed(int(time.monotonic() - state.run_started))`, guarded: if `state.run_started` is `None`, return `"unknown"` (defensive — notify sites must never crash on a missing timestamp).
- **Alert sites — append the time as a final line:**
  - `main.py:685` (done): `notify(config, f"All milestones done: {project_dir.name}\nRan for {_run_elapsed()}", "done")`
  - `main.py:780` (PipelineStopError): message gains `\nRan for {_run_elapsed()}` after the existing first-line excerpt.
  - `main.py:787` (RateLimitError): same.
- **Do not touch** the four `milestone` notify calls (`main.py:287,399,547,652`).
- The early-return path in `_run_dynamic_loop` ("All milestones are done!" printed at startup when nothing is pending) sends no alert — unchanged: a run that did no work needs no time report.
- **Verify:** run against a target project with an empty-ish roadmap where one milestone fails fast (or temporarily set `max_iterations: 1`); the stop alert must end with `Ran for <Nm Ns>`; complete the milestone and re-run to exhaustion; the done alert must end with the same format.

## What NOT to do

- Do not add run time to `milestone` alerts — per-milestone time lives in the roadmap and git history; duplicating it into Telegram adds noise to the one channel used for run-level accounting.
- Do not restructure `_with_caffeinate` or move its console prints — the alert path reads its own timestamp from `state`, keeping the two concerns independent.
- Do not add new alert types or config keys — the existing `stop` / `done` types and `telegram_alerts` filtering stay as-is.
