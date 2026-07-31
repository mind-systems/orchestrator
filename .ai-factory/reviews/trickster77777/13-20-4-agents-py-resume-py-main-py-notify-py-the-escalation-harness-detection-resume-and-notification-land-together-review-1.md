# Code Review: 20.4 — the escalation harness

**Files reviewed:** `orchestrator/agents.py`, `orchestrator/resume.py`, `orchestrator/main.py`, `orchestrator/notify.py`, `orchestrator.json.example`, `tests/test_agents.py`, `tests/test_main.py`, `tests/test_notify.py` (each read in full), cross-checked against the spec `40-escalation-harness.md`, `prompts/escalation.md`, `docs/reference/configuration.md`, and `.ai-factory/ARCHITECTURE.md`.

**Verdict:** 🟢 Pass — the three surfaces land together, correctly and coherently. `uv run pytest` green (206 passed).

## What was checked

### A. Detection (`agents.py`)
- `EscalationError(Exception)` is a direct `Exception` subclass, a sibling of `PipelineStopError`, **not** a `HaltError` subclass. Verified at runtime: `issubclass(EscalationError, HaltError)` is `False`, `issubclass(EscalationError, Exception)` is `True`. The docstring states the rationale so it is not "fixed" into the `HaltError` tree by analogy.
- `_has_escalation` reuses `_has_signal(text, "ESCALATION")` — the exact-line-in-last-5-lines shape, identical to the `PLAN_REVIEW_PASS`/`REVIEW_PASS` checks and matching `prompts/escalation.md`'s convention.
- `_escalation_excerpt` pulls the first non-empty, non-heading line under `## Escalation`, returning `""` when the section is absent — a graceful degrade (empty excerpt, never a crash).
- All four methods wire detection **after** the artifact write / session record and **before** the existing PASS check: `plan()` and `implement()` check `plan_path`; `review()` and `review_plan()` check their review file first, short-circuiting the PASS check via the `raise`. `review()`/`review_plan()` keep their `bool` return type on the non-escalation path. No `except EscalationError` inside `agents.py`; `_classify_result` and `TestRunner` untouched. Sidecar written only via `_write_session` (ARCHITECTURE Key Principle #2 honored).

### Critical ordering property (traced end to end)
The escalation write (`step="escalated"`) must survive rather than be overwritten by `process_task`'s normal step-tracking. Confirmed at every call site: because the agent method `raise`s from inside itself, control never reaches the following `_write_session(plan_path, "step", ...)` in `process_task` — `planned:{counter}` (`main.py:280`), `planned:{attempt+1}` (`:309`), `implemented:{iteration}` (`:333`), and the verify-fail tag (`:352`) are all skipped. There is no `try/except` around the loop that could swallow the exception or overwrite the sidecar. So `escalated` persists, and resume halts again. This is the load-bearing invariant of the task and it holds.

### B. Resume (`resume.py`)
- `_validate_sidecar_step` treats `"escalated"` as always valid (no `:N`), placed after the recognized forms and before the unrecognized fallback; docstring updated.
- `_detect_step` returns `("escalated", 0, plan_path)` as an explicit `elif` inside the sidecar-dispatch block, before the disk heuristic — an escalated sidecar never reaches steps 3–7. Docstring step enumeration updated. Wrappers `_detect_task_step`/`_detect_test_task_step` untouched; the other five forms unchanged.

### C. Halt wiring + notification (`main.py`, `notify.py`, `.example`)
- `EscalationError` added to the `main.py:14` import.
- `process_task` raises `EscalationError(sessions.get("escalation", ...))` immediately after step detection, alongside the `done` branch, reusing the already-read `sessions` — before any agent is constructed.
- `cli()` gains a third `except EscalationError` arm, correctly ordered **before** the generic `except Exception` (so it cannot be shadowed), printing `ESCALATED — …`, notifying `"escalation"`, and exiting `0` — mirroring the `PipelineStopError`/`HaltError` arms.
- `notify.py` adds `_ESCALATION_ALERTS = {"escalation"}` and a 🔵 tier in the emoji chain; `_FAIL_ALERTS`/`_HALT_ALERTS` and the 🟢 default untouched. The 🔵 matches the existing `docs/reference/configuration.md:83` alert-table row (verified present).
- `orchestrator.json.example` lists `escalation` between the operational and success tokens; the gitignored `orchestrator.json` untouched.

### Tests
Genuine behavioral coverage, not hollow: sibling-class assertion; `_has_escalation`/`_escalation_excerpt` positive and absent cases; each of the four methods raising `EscalationError` with `step=="escalated"` and a non-empty `escalation` field via a monkeypatched `_run_claude` that writes the artifact; two regressions confirming `REVIEW_PASS`/`PLAN_REVIEW_PASS` with no marker behave as before (return `bool`, no escalated sidecar); `_validate_sidecar_step`/`_detect_step` recognition of `escalated`; `process_task` raising without constructing any agent and without `mark_done`/`_git_commit` (asserted via monkeypatched constructors that fail if called); the 🔵 notify tier.

## Minor, non-blocking observations
- `review()` re-reads the review file and re-checks `.exists()` after the escalation block (`agents.py:439–449`). Harmless redundancy; not worth a change.
- `_escalation_excerpt` yields `""` when the first line under `## Escalation` is itself a sub-heading, making the summary blank. This only weakens the human-readable detail; the marker still halts the run correctly. Acceptable as-is.

No correctness, security, or resume-safety defects found. On-disk sidecar format is additive (`step="escalated"`, new `escalation` field) — no migration needed, and existing markers (`implemented:N`, etc.) resume unchanged.

REVIEW_PASS
