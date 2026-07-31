# Plan: 20.4 — the escalation harness: detection, resume, and notification land together

## Context
Wire the `ESCALATION` marker (produced by 20.3's shared escalation engine) into an operational outcome: a new `EscalationError`, per-method detection in the four agent methods that writes the `escalated` sidecar, resume recognition of `escalated` as a terminal step, a `cli()` except arm, and a fourth 🔵 notification tier. Split apart these surfaces would let a resumed escalation silently re-run or surface as a bare traceback, so they ship as one unit.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Detection — `EscalationError` and per-method wiring (`agents.py`)

- [x] **Task 1: Declare `EscalationError` and an escalation-detection helper**
  Files: `orchestrator/agents.py`
  Add a new exception class `class EscalationError(Exception):` immediately after `PipelineStopError` (`:113-114`) — a **direct `Exception` subclass, a sibling of `PipelineStopError`, deliberately NOT a `HaltError` subclass**. Docstring must state the rationale so a future reader does not "fix" it into the `HaltError` tree by analogy with `RateLimitError`/`NetworkError`: escalation IS a judgment about the work (an agent concluded it cannot honestly proceed), whereas `HaltError` is explicitly "not a task failure" per `docs/concepts/outcomes.md`. Suggested body:
  ```python
  class EscalationError(Exception):
      """Raised when an agent cannot honestly produce its mandated output because
      the missing decision is outside its authority — escalation, not halt.
      A deliberate sibling of PipelineStopError, NOT a HaltError subclass: halt is
      'not a task failure', escalation IS a judgment. Do not move it under HaltError."""
  ```
  Alongside `_has_signal` (`:42-44`), add a detection helper reusing the exact same shape as the existing PASS-signal check (exact match against a non-blank-trimmed line within the last 5 lines) — either a new `_has_escalation(text: str) -> bool` that calls `_has_signal(text, "ESCALATION")`, or call `_has_signal(text, "ESCALATION")` directly at the call sites. The literal token is `ESCALATION` (matches `prompts/escalation.md`'s convention: the exact line `ESCALATION` at the end of the artifact, never mixed with `PLAN_REVIEW_PASS`/`REVIEW_PASS`).
  Also add a small helper to pull the one-line escalation excerpt from the artifact's `## Escalation` section (the first non-empty, non-heading line under `## Escalation`), for the sidecar summary in Task 2 — return an empty/placeholder string if the section is absent.

- [x] **Task 2: Wire `ESCALATION` detection into the four agent methods** (depends on Task 1)
  Files: `orchestrator/agents.py`
  In each of the four methods below, after the artifact is written (`_run_claude` returned and `_write_session(..., "planner"/"implementer", ...)` recorded the session) and **before** any existing return / PASS-signal check, read the artifact tail and check for `ESCALATION`. On a hit, in all four:
  1. Write the sidecar **only via `_write_session(plan_path, key, value)`** (per `.ai-factory/ARCHITECTURE.md` Key Principle #2 — `_write_session` is the sole sidecar writer; never write the `.json` directly): set field `"escalation"` to a short JSON-serializable string summary (agent role + one-line excerpt from `## Escalation` + artifact path) and set `"step"` to `"escalated"`.
  2. `raise EscalationError(f"...")` quoting the artifact path and the one-line summary. The raise **replaces** the return for this path — do NOT return a third value; `review()`/`review_plan()` keep their `bool` return type for the pass/fail case, exactly as an uncaught `NetworkError`/`RateLimitError` already replaces the return today.
  Per-method placement:
  - `PlannerReviewer.plan()` (`:334-362`): after `_write_session(plan_path, "planner", ...)` (`:362`), check `plan_path`'s tail.
  - `PlannerReviewer.review()` (`:364-406`): after `_write_session(plan_path, "planner", ...)` (`:401`) and before the `_has_signal(review_path.read_text(), "REVIEW_PASS")` check (`:404-405`) — check `review_path` for `ESCALATION` first; if present, do not fall through to the `REVIEW_PASS` check.
  - `PlanReviewer.review_plan()` (`:424-446`): before the `_has_signal(review_path.read_text(), "PLAN_REVIEW_PASS")` check (`:444-445`), check `review_path`.
  - `Implementer.implement()` (`:465-491`): after `_write_session(plan_path, "implementer", ...)` (`:491`), check `plan_path`'s tail (the implementer writes its escalation into the plan file it owns).
  Guards: do NOT add any `except EscalationError` inside `agents.py` — it must propagate uncaught to `cli()` (Phase 3). Do NOT touch `_classify_result` (`:69-97`) — unrelated process-outcome classifier. Do NOT touch `TestRunner` (`:494+`) — no LLM session, nothing to escalate.

- [x] **Task 3: Unit tests for detection + sidecar write** (depends on Task 2)
  Files: `orchestrator/tests/test_agents.py`
  - `from orchestrator.agents import EscalationError, HaltError` then `assert not issubclass(EscalationError, HaltError)`.
  - For each of `plan`/`review`/`review_plan`/`implement`: a written artifact ending with a `## Escalation` section + the `ESCALATION` marker causes the method to raise `EscalationError`, and the plan-path `.json` sidecar ends up with `step == "escalated"` and a non-empty `escalation` field. Stub/monkeypatch `_run_claude` so the test controls the artifact content without a real CLI call (follow the existing test patterns in this file for faking `_run_claude`/artifact writes).
  - Regression: an artifact ending with `REVIEW_PASS`/`PLAN_REVIEW_PASS` and NO `ESCALATION` line behaves exactly as before (returns the existing `bool`, no raise, no `escalated` sidecar).

### Phase 2: Resume — `escalated` halts again instead of retrying (`resume.py`)

- [x] **Task 4: Recognize `escalated` as a terminal, unindexed step** (depends on Task 1)
  Files: `orchestrator/resume.py`
  1. In `_validate_sidecar_step` (`:11-62`): add a branch recognizing `"escalated"` as always valid, placed after the existing `plan_review_failed:`/`plan_reviewed`/`<fail_prefix>` branches and **before** the `unrecognized → return as-is` fallback (`:61-62`):
     ```python
     if step_value == "escalated":
         return step_value
     ```
     `escalated` carries **no** `:N` suffix — escalation is terminal, not iteration-indexed. Update the docstring (`:20-29`) to document the new branch alongside the existing bullets.
  2. In `_detect_step` (`:84-173`): inside the `if step_value:` block (`:126-141`), add an `elif step_value == "escalated":` branch returning `("escalated", 0, plan_path)`, placed before the `# unrecognized → fall through to heuristic` comment (`:141`) so an escalated sidecar never reaches the disk-heuristic steps 3-7 (`:143-173`). Update the docstring's step enumeration (`:91`, currently `"plan", "plan_review", "implement", <verify_step>, "done"`) to include `"escalated"`.
  Guards: do NOT add an `escalated` case to the thin wrappers `_detect_task_step`/`_detect_test_task_step` (`:176-203`) — both already route through `_detect_step`. Do NOT touch any other recognized form (`planned:N`, `implemented:N`, `plan_review_failed:N`, `plan_reviewed`, `<fail_prefix>N`) or `_plan_is_stale` (`:65-81`). Do NOT make `escalated` resumable into a fresh attempt.

- [x] **Task 5: Unit tests for resume recognition** (depends on Task 4)
  Files: `orchestrator/tests/test_main.py` (or a new `tests/test_resume.py`, matching wherever `_validate_sidecar_step`/`_detect_step` are currently tested)
  - A sidecar with `"step": "escalated"` validates as `"escalated"` via `_validate_sidecar_step`, and `_detect_step` returns `("escalated", 0, plan_path)`.
  - All pre-existing `_validate_sidecar_step`/`_detect_step` cases stay unchanged.

### Phase 3: Halt wiring in `main.py` (`process_task` + `cli()`)

- [x] **Task 6: Terminal `escalated` branch and `cli()` except arm** (depends on Task 1, Task 4)
  Files: `orchestrator/main.py`
  1. Import line (`:14`): add `EscalationError` to `from .agents import HaltError, Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, TestRunner, _read_sessions, _write_session`.
  2. In `process_task` (`:198-...`): add an `escalated` branch immediately alongside the existing `if step == "done":` branch (`:236-244`), right after the `_detect_step` call (`:220-224`) and the `sessions`/`elapsed_offset` read (`:227-231`) — reuse that same `sessions` read, do not re-read:
     ```python
     if step == "escalated":
         raise EscalationError(sessions.get("escalation", "(no escalation detail recorded)"))
     ```
     This mirrors the `done` branch's shape (a terminal state handled before any agent is constructed) and makes a resumed-but-unresolved escalation fail loud and immediately instead of falling through to plan/implement/verify.
  3. In `cli()` (`:480-514`): add a third outcome-specific `except EscalationError as e:` arm, structurally identical to the existing `PipelineStopError`/`HaltError` arms (`:501-514`), placed **after** `except HaltError` (ordering is not load-bearing — `EscalationError` is a plain `Exception` sibling, cannot shadow or be shadowed by the `HaltError` arm; last only for severity-reading order):
     ```python
     except EscalationError as e:
         print(f"\n{'='*60}")
         print(f"ESCALATED — {e}")
         print(f"{'='*60}")
         msg = str(e).splitlines()[0]
         notify(config, f"Orchestrator escalated: {project_dir.name}\n{msg}\n{_run_summary()}", "escalation")
         sys.exit(0)
     ```
  Guards: do NOT touch the existing `done` branch, the generic `except Exception`, or any other branch. `EscalationError` must be caught here explicitly, not via the generic handler.

- [x] **Task 7: Unit test for the resumed-escalation halt** (depends on Task 6)
  Files: `orchestrator/tests/test_main.py`
  `process_task`, given a plan path whose sidecar has `"step": "escalated"`, raises `EscalationError` **without** constructing any agent (`PlannerReviewer`/`Implementer`/`PlanReviewer` never instantiated) and **without** calling `mark_done`/`_git_commit`. Follow the existing `process_task` test setup/monkeypatching in this file.

### Phase 4: Notification — a fourth alert tier (`notify.py` + config example)

- [x] **Task 8: Add the 🔵 escalation alert tier**
  Files: `orchestrator/notify.py`
  Add a third tier below `_HALT_ALERTS` (`:18`):
  ```python
  # Alert types that report an escalation — a judgment the run cannot make on its own.
  _ESCALATION_ALERTS = {"escalation"}
  ```
  Extend `notify()`'s emoji selection (`:27`) to a three-way chain plus the green default:
  ```python
  emoji = (
      "🔴" if alert_type in _FAIL_ALERTS
      else "🟡" if alert_type in _HALT_ALERTS
      else "🔵" if alert_type in _ESCALATION_ALERTS
      else "🟢"
  )
  ```
  (🔵 matches the row already present in `docs/reference/configuration.md`'s alert table — do not edit that doc; only make the code match it.) Guards: do NOT touch `_FAIL_ALERTS`/`_HALT_ALERTS` membership or the `"task"`/`"done"` 🟢 success path.

- [x] **Task 9: Add the `escalation` token to the example config**
  Files: `orchestrator/orchestrator.json.example`
  Extend `telegram_alerts_example_all` (`:11`) from `["task-fail", "stop", "task", "done"]` to `["task-fail", "stop", "escalation", "task", "done"]` — same list-literal style, `escalation` inserted between the operational tokens and the success tokens (matching `docs/reference/configuration.md`'s alert-table row order). Guard: do NOT touch the gitignored `orchestrator.json` (per-user), only `.example`; do not change `telegram_alerts` (empty default).

- [x] **Task 10: Unit test for the escalation emoji tier** (depends on Task 8)
  Files: `orchestrator/tests/test_notify.py`
  Matching however the existing `_FAIL_ALERTS`/`_HALT_ALERTS` cases are tested today: the `"escalation"` alert type resolves to the new 🔵 tier, not the 🟢 default. If the existing tests assert on the sent-message payload, assert the 🔵 prefix; if they assert on `_ESCALATION_ALERTS` membership, follow that shape.

### Phase 5: Full-suite verification

- [x] **Task 11: `uv run pytest` green** (depends on all above)
  Files: (no edits — verification)
  Run `uv run pytest` from `orchestrator/` and confirm the whole suite is green, covering the new detection, resume, notification, and `cli()`/`process_task` tests plus no regression to the pre-existing pass-signal, `_validate_sidecar_step`/`_detect_step`, and `notify` cases. Also confirm `python -c "from orchestrator.agents import EscalationError, HaltError; assert not issubclass(EscalationError, HaltError)"` passes.
