# Plan: 26.1 — the plan-review signal is held once

## Context
`PLAN_REVIEW_PASS` is spelled out as a string literal in four readers across `agents.py`, `pipeline.py` and `resume.py`. This task gives it one home, a `PLAN_REVIEW_PASS` constant in `orchestrator/protocol.py`, and makes every reader import it. Nothing changes in behaviour: each check keeps its current form (`endswith` stays `endswith`, `_has_signal` stays `_has_signal`; switching the `endswith` checks to `_has_signal` is 26.2's job), and the plan reviewer's prompt text stays byte-identical. Spec: `.ai-factory/specs/trickster77777/0075-the-plan-review-signal-is-held-once.md`. Governing spec: `docs/pipeline.md` § Completion signals. That doc names the signal but gives it no home, so it stays true without edits.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Hold the constant

- [x] **Define `PLAN_REVIEW_PASS` in `protocol.py`**
  Files: `orchestrator/protocol.py`
  Add a module-level constant `PLAN_REVIEW_PASS = "PLAN_REVIEW_PASS"` after the imports and before `_has_signal`, which keeps it with the completion-signal and escalation recognition helpers. The constant lives in `protocol` and not in `agents` because `resume` reads it, and `resume` must not import `agents`. Leave everything else as it is: `ESCALATION` stays a literal inside `_has_escalation` and does not become a constant, and the bodies of `_has_signal`, `_has_escalation`, `_escalation_excerpt` and the sidecar helpers do not change. `protocol` still imports nothing from the package.

### Read it where the literal was

- [x] **`agents.py` reads the constant** (depends on Define `PLAN_REVIEW_PASS` in `protocol.py`)
  Files: `orchestrator/agents.py`
  Add `PLAN_REVIEW_PASS` to the existing `from .protocol import ...` line, keeping the names in alphabetical order with uppercase first: `PLAN_REVIEW_PASS, _escalation_excerpt, _has_escalation, _has_signal, _write_session`. Then make two edits in `PlanReviewer.review_plan`:
  - Change the prompt line `f"If the plan is solid, end the review file with PLAN_REVIEW_PASS on its own line.\n"` to interpolate the constant: `f"If the plan is solid, end the review file with {PLAN_REVIEW_PASS} on its own line.\n"`. This follows the same pattern `PlannerReviewer.review` already uses with `{REVIEW_VERIFY.pass_signal}`. The rendered prompt text must stay identical.
  - Change the final `return _has_signal(review_text, "PLAN_REVIEW_PASS")` to `return _has_signal(review_text, PLAN_REVIEW_PASS)`.
  Leave `REVIEW_VERIFY`, `TEST_RUN_VERIFY` and their `pass_signal` values unchanged. `REVIEW_PASS` and `TEST_PASS` stay on their verify kinds.

- [x] **`pipeline.py` reads the constant** (depends on Define `PLAN_REVIEW_PASS` in `protocol.py`)
  Files: `orchestrator/pipeline.py`
  Extend `from .protocol import _read_sessions, _write_session` to `from .protocol import PLAN_REVIEW_PASS, _read_sessions, _write_session`. In `process_task`, the plan-review safety guard (the block under the comment `# Safety guard: ensure a passing plan review exists before implementing`) contains `.read_text().strip().endswith("PLAN_REVIEW_PASS")`. Replace the literal with `PLAN_REVIEW_PASS` and keep the `.strip().endswith(...)` form exactly as it is.

- [x] **`resume.py` reads the constant** (depends on Define `PLAN_REVIEW_PASS` in `protocol.py`)
  Files: `orchestrator/resume.py`
  Extend `from .protocol import _read_sessions` to `from .protocol import PLAN_REVIEW_PASS, _read_sessions`. Make two replacements, each keeping its `.strip().endswith(...)` form:
  - In `_validate_sidecar_step`, the `plan_reviewed` branch has `f.read_text().strip().endswith("PLAN_REVIEW_PASS")` inside the `any(...)` generator. Change it to `.endswith(PLAN_REVIEW_PASS)`.
  - In `_detect_step`, step 4 (comment `# 4. Latest plan-review didn't pass → plan needs revision`) has `plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS")`. Change it to `.endswith(PLAN_REVIEW_PASS)`.
  Leave the docstring's prose mention of `PLAN_REVIEW_PASS` in `_validate_sidecar_step` as it is: it names the protocol signal, it is not a check, and 26.2 rewrites that docstring. `resume` still imports only from `ports` and `protocol` and never from `agents`.

### Verify neutrality

- [x] **Confirm the literal is gone from the readers and the suite still passes** (depends on all tasks above)
  Files: none (verification only)
  Run `grep -n '"PLAN_REVIEW_PASS"' orchestrator/*.py`. The only hit should be the definition in `protocol.py`. Mentions in `orchestrator/prompts/*.md` and in `tests/` stay unchanged: the prompt files keep the protocol literal, and the test fixtures write the signal as text. Run `uv run pytest`, which must pass with no test added or changed.
