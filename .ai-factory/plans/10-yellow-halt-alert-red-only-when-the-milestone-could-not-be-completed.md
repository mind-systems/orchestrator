# Plan: Yellow `halt` alert — red only when the milestone could not be completed

## Context
Split terminal alert colour by cause, not exception class: 🔴 `stop` stays only for a milestone that could not be completed, while every operational stop (usage breach, resume-past-max, rate limit, manual Ctrl+C, any unhandled exception) becomes a 🟡 `halt` routed through a new `HaltError`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Exception hierarchy & colour tiers

- [x] **Task 1: Introduce `HaltError` and reparent `RateLimitError`**
  Files: `orchestrator/agents.py`
  Add `class HaltError(Exception)` with a docstring ("an operational halt that is not a milestone failure — 🟡"). Change `class RateLimitError(Exception)` (`agents.py:69`) to `class RateLimitError(HaltError)`. Define `HaltError` before `RateLimitError` so the subclass resolves. Leave `class PipelineStopError(Exception)` (`agents.py:73`) unchanged — it now means exactly "the milestone could not be completed" (🔴). Do not touch the two `raise RateLimitError(...)` sites (`agents.py:205,218`).

- [x] **Task 2: Three-tier emoji pick in `notify()`**
  Files: `orchestrator/notify.py`
  Keep `_FAIL_ALERTS = {"stop"}` → 🔴. Add `_HALT_ALERTS = {"halt"}` → 🟡. Replace the emoji expression at `notify.py:24` with `emoji = "🔴" if alert_type in _FAIL_ALERTS else "🟡" if alert_type in _HALT_ALERTS else "🟢"`. No call-site or signature changes; `halt` remains gated by its own `telegram_alerts` entry via the existing membership check.

### Phase 2: Reach config from the force-quit handler

- [x] **Task 3: Stash `config`/`project_dir` in shared state**
  Files: `orchestrator/state.py`, `orchestrator/main.py`
  In `state.py`, under the existing `from __future__ import annotations`, add a `TYPE_CHECKING` block importing `OrchestratorConfig` from `.config` and `Path` from `pathlib` (no runtime import — avoids a cycle), then declare module globals alongside `run_started`: `config: OrchestratorConfig | None = None` and `project_dir: Path | None = None`. In `main.py`, set `state.config = config` and `state.project_dir = project_dir` as the first statements of both `run_implement()` (`main.py:742`) and `run_test()` (`main.py:752`), next to `state.run_started = time.monotonic()` and before `signal.signal(signal.SIGINT, _handle_sigint)`.

### Phase 3: Re-point non-failure raises and manual-stop alerts

- [x] **Task 4: Move operational raises to `HaltError`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Import `HaltError` alongside the existing names from `.agents` (`main.py:13`). Change these four `PipelineStopError` raises to `HaltError` — they are operational halts where nothing was judged: `_check_usage_limits` session breach (`main.py:63`) and weekly breach (`main.py:67`); resume-past-max in implement (`main.py:357`) and in test (`main.py:622`). Leave every other `PipelineStopError` raise unchanged (`main.py:335,350,390,601,615,649,697`) — those are genuine milestone-not-completed failures (🔴).

- [x] **Task 5: Emit `halt` on manual Ctrl+C (graceful + force-quit)** (depends on Task 3)
  Files: `orchestrator/main.py`
  Graceful stop: in `_run_dynamic_loop`, after the existing `print("\n>>> Stop requested — halting.")` under `if state.stop_requested:` (`main.py:714-715`), add `notify(config, f"Orchestrator stopped (manual): {project_dir.name}\nRan for {_run_elapsed()}", "halt")` (both `config` and `project_dir` are in scope). Force quit: in `_handle_sigint`'s force-quit branch (`main.py:22-25`), after `kill_active_child()` and before `sys.exit(1)`, add:
  ```python
  if state.config is not None and state.project_dir is not None:
      notify(state.config, f"Orchestrator force-quit: {state.project_dir.name}\nRan for {_run_elapsed()}", "halt")
  ```
  Guard on `is not None` so a signal arriving before `run_*` sets state never crashes the handler.

### Phase 4: `cli()` exception routing

- [x] **Task 6: Add `HaltError` and generic-`Exception` handlers to `cli()`** (depends on Tasks 1, 4)
  Files: `orchestrator/main.py`
  In `cli()` (`main.py:783-796`), keep `except PipelineStopError as e:` first, unchanged (alert `"stop"` 🔴, `sys.exit(0)`). Delete the standalone `except RateLimitError as e:` block (`main.py:790-796`) — `RateLimitError` is now a `HaltError` subclass and its message already names the sub-cause. Add, in order after the `PipelineStopError` handler:
  - `except HaltError as e:` — `msg = str(e).splitlines()[0]`; print a `HALTED — {e}` banner (mirroring the existing banners); `notify(config, f"Orchestrator halted: {project_dir.name}\n{msg}\nRan for {_run_elapsed()}", "halt")`; `sys.exit(0)`.
  - `except Exception as e:` (last) — `notify(config, f"Orchestrator error: {project_dir.name}\n{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}\nRan for {_run_elapsed()}", "halt")`, then bare `raise` so the traceback and non-zero exit survive. Do not swallow. `SystemExit`/`KeyboardInterrupt` derive from `BaseException` and are intentionally not caught here, so the force-quit `sys.exit(1)` and graceful return are unaffected.

## Commit Plan
- **Commit 1** (after tasks 1-2): "Add HaltError hierarchy and three-tier alert emoji"
- **Commit 2** (after tasks 3-5): "Route operational halts and manual stops to yellow halt alerts"
- **Commit 3** (after task 6): "Split cli() exception routing into stop, halt, and re-raised error"
