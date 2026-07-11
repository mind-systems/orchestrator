# Terminal alert format: uniform fail lines + per-run done counter

One concern: what a terminal Telegram alert says. Two changes to it: the failure first lines become uniform, and every terminal alert gains the run's completed-milestone count.

## Current state

**Fail lines differ per site**, and only the first line reaches Telegram (`cli()` takes `str(e).splitlines()[0]`, `main.py:406`):

- plan-review exhaustion (`main.py:207`): `Plan failed review after {max_iterations} attempt(s).`
- code-review exhaustion (`IMPLEMENT_MODE.max_iterations_message`, `main.py:53`): `Max iterations ({n}) reached without REVIEW_PASS.`
- test-run exhaustion (`TEST_MODE.max_iterations_message`, `main.py:69`): `Tests failed after {n} iteration(s).`

Three formats for one event class; attempt counts add noise the alert reader doesn't act on.

**No run context beyond elapsed time**: a remote reader of `Plan failed` can't tell "died on the first milestone — something systemic" from "normal attrition after six done" without opening the machine. The counter answering that exists implicitly (number of `mark_done` calls this process) but is not tracked.

## Change

### 1. Uniform fail first lines

- plan-review exhaustion → `Plan failed` (plan phase is shared by both modes)
- implement-mode review exhaustion → `Implement failed`
- test-mode run exhaustion → `Test failed`

No attempt counts, no signal names. Everything after the first line stays: `\n\nLast review: {path}\n\n{content}` (and the test-run variant) — the console `STOPPED — {e}` block and `/milestone-rescue` diagnostics lose nothing. The invariant-violation raises (no passing plan review `main.py:222`, unchecked-checkbox loop guard `main.py:309`) keep their wording — protocol violations, not phase failures.

### 2. Per-run done counter in every terminal alert

- `state.py` gains `milestones_done: int = 0`; reset to `0` at the top of `run_implement`/`run_test` (beside `run_started`).
- Incremented after `mark_done` in **both** completion paths of `process_milestone`: the resume-`done` early return (`main.py:149-156`) and the normal completion (`main.py:266-274`). `mark_skipped` is NOT counted — the number answers "how much work did this run actually complete".
- New helper in `runtime.py`: `_run_summary() -> str` returning `Ran for {_run_elapsed()} · {state.milestones_done} milestones done` — the single home of the format. Every **terminal** alert replaces its `Ran for {_run_elapsed()}` fragment with `_run_summary()`:
  - all-milestones-done (`main.py:303`, green `done`)
  - manual-stop after loop (`main.py:328`, yellow `stop`)
  - `PipelineStopError` handler (`main.py:407`, red `milestone-fail`)
  - `HaltError` handler (`main.py:414`, yellow `stop`)
  - generic-`Exception` handler (`main.py:419`, yellow `stop`)
  - force-quit (`runtime.py:20`, yellow `stop`)
- Per-milestone green `milestone` alerts untouched — a counter there is meaningless.

Resulting messages:

```
🔴 Orchestrator stopped: mind_mobile
Plan failed
Ran for 1h 42m 17s · 4 milestones done
```

```
🟡 Orchestrator stopped (manual): mind_mobile
Ran for 2h 5m 3s · 3 milestones done
```

**Pinned semantics: the counter is per-run, not per-roadmap** — after interrupt + rerun it restarts at 0; it deliberately does not read the roadmap's total `[x]` count and must not be worded to look like roadmap progress (no "N of M").

## Files & types

- edit `orchestrator/main.py` (three message sites; two increment sites; five terminal-alert call sites)
- edit `orchestrator/state.py` (`milestones_done`)
- edit `orchestrator/runtime.py` (`_run_summary`, force-quit call site)
- add tests in `tests/`

## Guards

- No changes to `notify.py`, alert types, emoji mapping, or the `cli()` first-line extraction.
- No milestone title in the alert — separate, explicitly deferred decision.
- Literal suffix is exactly ` · {n} milestones done` — no singular special-casing, no percentages.
- `state.milestones_done` is process state like `run_started` — never persisted to the sidecar.

## Verification

- `uv run pytest` green; new unit tests pin `_run_summary` formatting (counter interpolation; `run_started is None` → `Ran for unknown · 0 milestones done`) — silent-failure surface (wrong number, no crash). The increment paths ride the existing detector/loop tests' territory; live check covers them.
- Live: run a two-milestone roadmap where the second fails plan review with `max_iterations: 1` → red alert reads `Plan failed` / `Ran for … · 1 milestones done`; Ctrl+C during a run → yellow manual-stop alert carries the counter.
