# Plan: Extract main.py helpers into cohesive modules

## Context
Split three cohesive clusters out of `orchestrator/main.py` into their own modules (`usage.py`, `resume.py`, `runtime.py`) so each has one reason to change; `main.py` keeps the pipeline, loops, `_git_commit`, `run_*`, and `cli`. Pure move, zero behaviour change.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Constraints (from spec `.ai-factory/specs/09-extract-main-modules.md`)
- **Move only, no behaviour change.** Identical console output, artifact names, sidecar `step` progression, signals, and usage gating. If any "tidy-up" would alter behaviour, don't do it.
- **Downward imports only, no cycle.** New modules import from `agents`/`config`/`notify`/`state` and stdlib — never from `main`. `main` imports the moved callables from the new modules.
- **Do NOT touch** `agents.py`, `notify.py`, prompts, the artifact protocol, or `ARCHITECTURE.md`.
- **Do NOT extract** `_git_commit`, the loops, `process_milestone`, `run_*`, or `cli` — they stay in `main.py`.

### Assumption: detector wrappers and the `Mode` constants
`_detect_milestone_step` / `_detect_test_milestone_step` are thin wrappers used only by the test suite (production calls `_detect_step` directly at `main.py:346`). Today they read `IMPLEMENT_MODE`/`TEST_MODE`, which live in `main.py` and stay there (the pipeline's `Mode` descriptor). Since `resume.py` must not import `main` (cycle), the two wrappers move to `resume.py` and pass the four detector params as **literals identical to the current `Mode` field values** (see Task 2). This is the necessary consequence of the no-cycle + cohesion boundary; the values are the stable step-vocabulary and must match `IMPLEMENT_MODE`/`TEST_MODE` exactly.

## Tasks

### Phase 1: Create the three new modules

- [x] **Task 1: Create `usage.py` — usage-threshold gating**
  Files: `orchestrator/usage.py`
  Move `_parse_pct` and `_check_usage_limits` verbatim out of `main.py` (lines 82–121). Add module-level constants `SESSION_PATTERN = r"Current session:\s+(\d+(?:\.\d+)?)%"` and `WEEKLY_PATTERN = r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"`, and have `_check_usage_limits` reference them in place of the two inline regex literals (currently `main.py:97–98`) — same strings, so no behaviour change. Imports: `from __future__ import annotations`, `import re`, `import subprocess`, `from .config import OrchestratorConfig`, `from .agents import HaltError`. Keep `_check_usage_limits` raising `HaltError` (unchanged from task 05).

- [x] **Task 2: Create `resume.py` — resume / step-detection**
  Files: `orchestrator/resume.py`
  Move `_validate_sidecar_step` (lines 166–212), `_detect_step` (215–301), `_detect_milestone_step` (304–313), and `_detect_test_milestone_step` (316–325) verbatim. For the two wrappers, replace the `IMPLEMENT_MODE.*` / `TEST_MODE.*` field reads with the equivalent literals so `resume.py` needs no `main` import:
    - implement wrapper → `verify_step="review"`, `verify_fail_tag="review_failed:"`, `output_suffix="-review-{n}.md"`, `pass_signal="REVIEW_PASS"`
    - test wrapper → `verify_step="test_run"`, `verify_fail_tag="test_run_failed:"`, `output_suffix="-test-{n}.txt"`, `pass_signal="TEST_PASS"`
  Add a short comment on each wrapper noting the literals mirror `main.IMPLEMENT_MODE`/`TEST_MODE`. Imports: `from __future__ import annotations`, `import subprocess`, `from pathlib import Path`, `from .agents import _read_sessions`.

- [x] **Task 3: Create `runtime.py` — run/signal/process lifecycle**
  Files: `orchestrator/runtime.py`
  Move `_handle_sigint` (lines 71–79), `_fmt_elapsed` (490–493), `_run_elapsed` (496–499), and `_with_caffeinate` (502–527) verbatim. `_handle_sigint` keeps calling `kill_active_child()`, `notify(state.config, …, "halt")`, and `_run_elapsed()`; `_run_elapsed` keeps reading `state.run_started`; `_with_caffeinate` keeps using `_fmt_elapsed` and `signal.SIGTERM`. Imports: `from __future__ import annotations`, `import signal`, `import subprocess`, `import sys`, `import time`, `from . import state`, `from .notify import notify`, `from .agents import kill_active_child`.

### Phase 2: Rewire `main.py` and the tests

- [x] **Task 4: Repoint `main.py` to the new modules** (depends on Tasks 1–3)
  Files: `orchestrator/main.py`
  Delete the moved function bodies (`_handle_sigint`, `_parse_pct`, `_check_usage_limits`, `_validate_sidecar_step`, `_detect_step`, `_detect_milestone_step`, `_detect_test_milestone_step`, `_fmt_elapsed`, `_run_elapsed`, `_with_caffeinate`). Add imports:
    - `from .usage import _check_usage_limits`
    - `from .resume import _detect_step`
    - `from .runtime import _handle_sigint, _with_caffeinate, _run_elapsed`
  Clean now-unused imports: drop `import re` (only `_parse_pct` used it) and drop `kill_active_child` from the `.agents` import line (only `_handle_sigint` used it). Keep `import signal` (still registers the handler via `signal.signal(signal.SIGINT, _handle_sigint)` at the two `run_*` entry points), and keep `subprocess`, `sys`, `time`, `_read_sessions`, `_write_session`, `HaltError`, `PipelineStopError`. Leave `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `process_milestone`, the loops, `_git_commit`, `run_implement`, `run_test`, and `cli` in place, and leave the `_detect_step(…)` call at the former line 346 unchanged (it now resolves to the imported symbol).

- [x] **Task 5: Repoint the moved tests' imports (Class-A drift only)** (depends on Task 4)
  Files: `tests/test_main.py`
  Change only the import path of the moved symbols — never weaken an assertion:
    - `_parse_pct`, `_check_usage_limits` now come from `orchestrator.usage`.
    - `_validate_sidecar_step`, `_detect_milestone_step`, `_detect_test_milestone_step` now come from `orchestrator.resume`.
    - `process_milestone` stays imported from `orchestrator.main`.
  Add `from orchestrator import usage as usage_module` and repoint the one monkeypatch target in `test_check_usage_limits_raises_halt_error_over_threshold` from `main_module.subprocess` to `usage_module.subprocess` (same Class-A path drift — the symbol changed modules; do not alter the assertion). Update the module docstring on line 1 if it names the moved functions. (Splitting into `test_usage.py` / `test_resume.py` is an allowed alternative, but in-place repointing is the lowest-risk path and satisfies "only import lines changed".)

## Verify
- `uv run pytest` green **before and after** — record it is green before starting, and confirm green after Task 5.
- No behaviour change: identical console output, artifact names, sidecar `step` progression, signals, and usage gating.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Add usage, resume, and runtime modules"
- **Commit 2** (after tasks 4-5): "Move main.py helpers into cohesive modules and repoint tests"
