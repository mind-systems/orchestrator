# Extract main.py helpers into cohesive modules

**Date:** 2026-07-09
**Source:** conversation context

## Problem today

`main.py` mixes the milestone pipeline with unrelated concerns — usage gating, resume/step detection, signal & process lifecycle. Line count is a symptom; the real smell is that one module owns many independent responsibilities. A 600-line grab-bag is no better than an 800-line one. Split the cohesive clusters into their own modules so each has one reason to change and the pipeline core reads clean.

## The extraction (pure, behaviour-preserving)

Three cohesive clusters move out of `main.py`:

- **`usage.py`** — `_parse_pct`, `_check_usage_limits`, and the `SESSION_PATTERN` / `WEEKLY_PATTERN` constants. Self-contained usage-threshold gating.
- **`resume.py`** — `_validate_sidecar_step` and the step-detector (after task 06, the unified detector; if the two `_detect_*_step` names survive as wrappers, they move too). The "where did a prior run stop" logic.
- **`runtime.py`** — `_handle_sigint`, `_with_caffeinate`, `_fmt_elapsed`, `_run_elapsed`. Process/run lifecycle.

**Stays in `main.py`:** `process_milestone` (the unified pipeline), `_run_loop`, `_next_number`, `_git_commit`, `_run_dynamic_loop`, `_test_loop`, `_implement_loop`, `run_implement`, `run_test`, `cli`. `_git_commit` stays — it is only called from the pipeline tail; a 21-line `git.py` would be thinner than the coupling it removes.

Module names are suggestions; the concern boundaries are the contract.

## Ordering — this task runs LAST

Place it after tasks 05 and 06 in the queue. It reorganizes code those tasks modify:
- 05 changes `_handle_sigint` (adds the force-quit `halt` notify + `state.config`/`state.project_dir` reads) → `runtime.py` must move the final form.
- 06 unifies the detector → `resume.py` must move the final form.

Running last means the extraction touches settled code once, with no re-churn and no merge fight against 05/06.

## Imports and cycles

- `main.py` imports the moved callables from the new modules (e.g. `from .runtime import _handle_sigint, _with_caffeinate, _run_elapsed`; register the handler via `signal.signal(signal.SIGINT, _handle_sigint)` as today).
- New modules import downward only — `usage.py` uses `config` + its own `_parse_pct`; `runtime.py` uses `state`, `notify`, and `kill_active_child` from `agents`; `resume.py` uses `_read_sessions` from `agents` and stdlib. None import `main` — no cycle.

## Tests — existing suite is the net; update imports

No new tests: the moved surfaces are already covered (`_parse_pct`, `_validate_sidecar_step`, and the detectors in `tests/test_main.py`, completed by task 08). This task **updates the moved tests' imports** so they resolve to the new modules — `_parse_pct` → `orchestrator.usage`; `_validate_sidecar_step` and the detector(s) → `orchestrator.resume`. Either repoint the imports in `test_main.py` or split them into `test_usage.py` / `test_resume.py`. This is Class-A API drift (module path changed), not a behaviour change — never weaken an assertion to make it pass.

## Verify

- `uv run pytest` is green **before and after**, with only import lines changed in the moved tests.
- No behaviour change: identical console output, artifact names, sidecar `step` progression, signals, and usage gating. If any "tidy-up" would alter behaviour, don't.

## What NOT to do

- Do not change behaviour — this is a move only.
- Do not run before 05/06 — it depends on their final code.
- Do not extract `_git_commit`, the loops, or the pipeline — they stay in `main.py`.
- Do not touch `agents.py`, `notify.py`, prompts, or the artifact protocol.
