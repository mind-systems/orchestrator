# Yellow `halt` signal — red only when the milestone could not be completed

**Date:** 2026-07-09
**Source:** conversation context

## The axis

Colour is decided by **cause**, not by exception class:

- **🔴 `stop` — the milestone could not be completed.** The review loop (plan or code/test) ran its full attempt budget and never produced a PASS signature, or the milestone otherwise failed to reach `done`. This is the only red outcome. See `docs/failures-and-halts.md` / `docs/non-convergence.md`.
- **🟡 `halt` — everything else that ends a run.** Not a judgement about the work: usage-budget exhausted, resume misconfiguration, API quota, an unhandled infrastructure error, or a manual operator stop. The current milestone may have been fine.

`PipelineStopError` is currently raised for **both** causes, so the split cannot key off the exception class. Introduce a dedicated halt exception and re-point the non-failure raise sites to it.

## Details

### `agents.py` — halt exception hierarchy

- Add `class HaltError(Exception)` — an operational halt that is not a milestone failure (🟡).
- Make `class RateLimitError(HaltError)` (currently subclasses `Exception`) — an API-quota halt is one kind of `HaltError`; its two raise sites (`agents.py:205,218`) are unchanged.
- `PipelineStopError` keeps subclassing `Exception` and now means exactly one thing: **the milestone could not be completed** (🔴).

### `main.py` — re-point the non-failure `PipelineStopError` sites to `HaltError`

These are operational halts, not milestone failures → raise `HaltError` instead of `PipelineStopError` (import `HaltError` alongside the existing names):
- `main.py:63` and `:67` — session / weekly usage-threshold breach in `_check_usage_limits`. The run stops on the milestone boundary; no work was judged.
- `main.py:357` (implement) and `:622` (test) — resume iteration exceeds `max_iterations`. Surfaces right after start, before any implement attempt — nothing was attempted, nothing failed.

**Leave these as `PipelineStopError` (🔴 — milestone not completed):** `main.py:335` (plan failed review after max attempts, implement), `:350` (no passing plan review, implement safety), `:390` (max iterations without `REVIEW_PASS`, implement), `:601` (plan failed review, test), `:615` (no passing plan review, test safety), `:649` (tests failed after max iterations), `:697` (milestone checkbox still unchecked after processing — the milestone did not complete).

### `main.py` — `cli()` exception handlers

Order matters (most specific first):
- `except PipelineStopError as e:` — **unchanged**, alert type `"stop"` (🔴), `sys.exit(0)`.
- **Add** `except HaltError as e:` — `msg = str(e).splitlines()[0]`; `notify(config, f"Orchestrator halted: {project_dir.name}\n{msg}\nRan for {_run_elapsed()}", "halt")`; `sys.exit(0)`. `RateLimitError` is a subclass, so it is caught here — its message text (`…hit your limit…`) already identifies the sub-cause; the separate rate-limit handler is removed.
- **Add** `except Exception as e:` last — `notify(config, f"Orchestrator error: {project_dir.name}\n{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}\nRan for {_run_elapsed()}", "halt")`, then **`raise`** (alert, then let the traceback and non-zero exit survive — do not swallow). `SystemExit` / `KeyboardInterrupt` derive from `BaseException` and are not caught here, so the force-quit `sys.exit(1)` and the graceful return are unaffected.

### `main.py` — manual Ctrl+C paths emit `halt`

- Graceful stop, after the existing print at `main.py:714` (inside `_run_dynamic_loop`, which has `config` + `project_dir` in scope):
  `notify(config, f"Orchestrator stopped (manual): {project_dir.name}\nRan for {_run_elapsed()}", "halt")`.

### `state.py` + `main.py` — reach `config` from the force-quit handler

- `_handle_sigint(sig, frame)` has no `config`. Stash it: add module globals to `state.py` alongside `run_started` — `config: OrchestratorConfig | None = None` and `project_dir: Path | None = None` (annotate under the existing `from __future__ import annotations`; add a `TYPE_CHECKING` import of `OrchestratorConfig` and `Path`, no runtime import cycle).
- Set both as the first statements of `run_implement()` / `run_test()`, next to `state.run_started = time.monotonic()`, before `signal.signal(...)` is registered.
- In `_handle_sigint`'s force-quit branch, after `kill_active_child()` and before `sys.exit(1)`:
  ```python
  if state.config is not None and state.project_dir is not None:
      notify(state.config, f"Orchestrator force-quit: {state.project_dir.name}\nRan for {_run_elapsed()}", "halt")
  ```
  Guard on `is not None` (never crash a signal handler). `notify` is already a no-op when `halt` is absent from `telegram_alerts` or creds are missing, and swallows network errors (worst case ≤10 s Telegram timeout before the force quit completes).

### `notify.py` — three tiers

- Keep `_FAIL_ALERTS = {"stop"}` → 🔴.
- Add `_HALT_ALERTS = {"halt"}` → 🟡.
- Emoji pick: `"🔴" if alert_type in _FAIL_ALERTS else "🟡" if alert_type in _HALT_ALERTS else "🟢"`.

### Config

- `halt` is gated by its own `telegram_alerts` entry — an operator must add `"halt"` to receive yellow alerts. (The docs already carry the target `telegram_alerts` set and the colour semantics; **this task changes no docs** — see below.)

## Tests

The colour mapping and `cli()` exception routing are covered by a tests-first milestone (`.ai-factory/specs/07-notify-routing-tests.md`) that lands **before** this task — its new-behaviour assertions (yellow `halt`, `HaltError` routing) are red until this task turns them green. Keep those tests green; do not weaken them.

## Verify

- Config with `telegram_alerts` including `stop`, `halt`, `done` and valid creds.
- Non-convergence (`max_iterations: 1` on a failing milestone) → 🔴 `Orchestrator stopped: …`.
- Usage-threshold breach (set `usage_threshold_5h` very low) → 🟡 `Orchestrator halted: Session usage at …`.
- Resume with a sidecar `step` past `max_iterations` → 🟡 `Orchestrator halted: Resume at iteration …`.
- `RateLimitError` (simulate "hit your limit") → 🟡 `Orchestrator halted: …hit your limit…`.
- Ctrl+C once → after the current milestone: 🟡 `Orchestrator stopped (manual): …`. Ctrl+C twice → immediate 🟡 `Orchestrator force-quit: …`.
- Force a `RuntimeError` → 🟡 `Orchestrator error: RuntimeError: …`, traceback still prints.
- All-done → 🟢.

## What NOT to do

- Do not colour by exception class — `PipelineStopError` is red only because it now means "milestone not completed"; the usage / resume-past-max halts must move off it to `HaltError`.
- Do not swallow the generic exception — alert `halt`, then `raise`.
- Do not touch docs — `docs/failures-and-halts.md`, `docs/configuration.md`, `docs/how-it-works.md` already describe the target taxonomy and colours; this task is code-only.
- Do not recolor `milestone` / `done`, and do not touch the four `milestone` notify calls or `_with_caffeinate`.
