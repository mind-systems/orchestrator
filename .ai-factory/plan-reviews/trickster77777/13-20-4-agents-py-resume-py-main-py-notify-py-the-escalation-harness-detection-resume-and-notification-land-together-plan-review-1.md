# Plan Review: 20.4 — the escalation harness

**Files Reviewed:** plan + `agents.py`, `resume.py`, `main.py`, `notify.py`, `runtime.py`, `prompts/escalation.md`, `orchestrator.json.example`, spec `40-escalation-harness.md`, roadmap contract line 20.4, `docs/reference/configuration.md`, `.ai-factory/ARCHITECTURE.md`, existing tests
**Risk Level:** 🟢 Low

## Context Gates

- **Governing spec** (`.ai-factory/specs/trickster77777/40-escalation-harness.md`): the plan is a faithful, near-verbatim implementation of the three-section spec (A detection, B resume, C notification) plus the two verification phases. Every guard in the spec is carried into the plan (sibling-not-subclass, `_write_session`-only sidecar, no `except` in `agents.py`, no `:N` suffix on `escalated`, `.example` only, don't touch `configuration.md`). No conformance gap. ✅
- **ARCHITECTURE.md** (Key Principle #2, "Sidecar is isolated — `_read_sessions`/`_write_session` live in `agents.py` only"): Task 2 correctly mandates `_write_session` as the sole sidecar writer and forbids direct `.json` writes. Boundary aligned. ✅
- **Roadmap** (`roadmaps/trickster77777.md:103`, task 20.4): the plan matches the contract line's scope exactly — `EscalationError` sibling of `PipelineStopError`, four detection methods writing `escalation`/`step:"escalated"`, resume terminal step, `cli()` arm, fourth alert tier, `.example` token. The "one unit, not three" framing is preserved. ✅
- **RULES.md**: not present in this repo; no gate to run.

## Line-reference and API accuracy (all confirmed against ground truth)

- `agents.py`: `PipelineStopError` at `:113-114`, `_has_signal` at `:42-44`, `plan()` `:334-362`, `review()` `:364-406`, `review_plan()` `:424-446`, `implement()` `:465-491`, `_classify_result` `:69-97`, `TestRunner` `:494+`, `_write_session` sole writer — all accurate.
- `resume.py`: `_validate_sidecar_step` `:11-62` with the `unrecognized → return as-is` fallback at `:61-62`; `_detect_step` `:84-173` with the `if step_value:` block `:126-141` and the fall-through comment at `:141`; disk heuristics `:143-173`; docstring enumeration at `:91`; thin wrappers `:176-203`; `_plan_is_stale` `:65-81` — all accurate.
- `main.py`: import line `:14`, `process_task` at `:198`, `done` branch `:236-244`, `_detect_step` call `:220-223`, `sessions`/`elapsed_offset` read `:227-231`, `cli()` arms `:501-514` — all accurate.
- `notify.py`: `_HALT_ALERTS` at `:18`, emoji chain at `:27`, `_FAIL_ALERTS` at `:15` — accurate.
- `orchestrator.json.example`: `telegram_alerts_example_all` at `:11` is `["task-fail", "stop", "task", "done"]` — matches; the proposed insertion of `escalation` between operational and success tokens matches `configuration.md`'s alert-table row order (`:81-85`, which already carries the 🔵 `escalation` row — plan correctly leaves that doc untouched).
- Prerequisite 20.3 has landed: `prompts/escalation.md` exists and specifies the exact `ESCALATION` marker + `## Escalation` section the plan detects; all three agent classes already concatenate `escalation_prompt`. The plan's assumptions about the token and section heading are grounded.

## Correctness walkthrough (no blocking issues found)

- **Uncaught propagation is real.** `EscalationError` raised inside any of the four methods propagates through `process_task` → `_run_dynamic_loop` (no `except`) → `_implement_loop`/`_test_loop` (no `except`) → `_with_caffeinate` (re-raises after printing) → `run_implement`/`run_test` (no `except`) → `cli()`'s new `except EscalationError`. Confirmed no interceptor swallows it. The generic `except Exception` in `cli()` is correctly bypassed by the explicit sibling arm.
- **Resume terminal state is airtight.** On resume, an escalated task's plan file is uncommitted/modified, so `_plan_is_stale` returns False and it is adopted; step 2 reads `step:"escalated"`, `_validate_sidecar_step` returns it as-is, and the new `elif` in `_detect_step` returns `("escalated", 0, plan_path)` before any disk heuristic — so the escalated work never silently re-runs, exactly the spec's central invariant.
- **`sessions` reuse in the `process_task` escalated branch is safe.** The plan reuses the `:227-231` `sessions` read instead of re-reading (resolving the spec's snippet-vs-guard-note tension toward the guard at spec `:105`). For an escalated task `plan_path` exists, so `sessions` is populated; `sessions.get("escalation", "(no escalation detail recorded)")` degrades cleanly. `int(sessions.get("elapsed","0"))` also survives the case where escalation fired before `elapsed` was ever written (e.g. planner escalates on first plan) — no crash.
- **Sidecar key name is consistent** between writer (Task 2, field `"escalation"`) and reader (Task 6.2, `sessions.get("escalation")`).
- **Detection ordering** (ESCALATION checked before `REVIEW_PASS`/`PLAN_REVIEW_PASS`) matches the prompt's "never mix" contract and the spec's per-method placement.
- **Test placement is correct**: `test_agents.py` already fakes `_run_claude` and tests `_has_signal`; `test_main.py` already houses `_validate_sidecar_step`/`_detect_*`/`process_task` tests; `test_notify.py` records sent payloads and can assert the 🔵 prefix. Tasks 3/5/7/10 land where the existing patterns already live.

## Positive Notes

- The plan pins every guard as an explicit "do NOT" with a rationale, mirroring the spec — notably the sibling-not-`HaltError` design with the docstring-embedded rationale, which pre-empts a future "fix by analogy."
- It correctly recognizes that the resume branch and the `cli()` arm must ship with detection (otherwise a resumed escalation re-runs or surfaces as a bare traceback), matching the spec's "state strictly worse than no escalation" argument.
- Phase 5 adds both `uv run pytest` and the `issubclass` sibling assertion as an explicit final gate.

## Critical Issues

None.

PLAN_REVIEW_PASS
