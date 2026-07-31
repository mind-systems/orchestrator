# Escalation harness: `EscalationError`, resume recognition, and notification wiring

**Date:** 2026-07-29
**Source:** conversation context (`EscalationError` + detection, the resume branch, and the notification arm are one atomic unit, not three: detection alone lets a resumed escalated task silently re-run past the human decision it stopped for, and lets `EscalationError` fall into `cli()`'s generic `except Exception`, which re-raises into a bare traceback instead of a clean halt)

## Why these three surfaces ship together

Splitting detection from the other two produces a state strictly worse than not having escalation at all, not merely an incomplete one:

- **Detection without the resume branch:** `resume.py` has no branch for the sidecar `step` value `escalated` until section B lands. An unrecognized `step_value` falls through unchanged in `_validate_sidecar_step` and `_detect_step` falls through to the disk heuristic — a run resumed on an escalated task silently re-derives a plan/implement/verify state and re-runs the very work that just stopped for a human decision, exactly the outcome escalation exists to prevent.
- **Detection without the notification arm:** `main.py`'s `cli()` has exactly two outcome-specific `except` arms until section C lands — `except PipelineStopError` and `except HaltError`, both exiting cleanly via `sys.exit(0)`. `EscalationError` falls to the generic `except Exception` below them, which calls `notify(..., "stop")` and then `raise`s again — an unhandled-exception traceback, mislabeled as an operational stop, instead of the clean halt every other outcome gets.

## A. `EscalationError` + per-method detection + sidecar write

### Problem today

`agents.py:100-114` declares the run's existing exception hierarchy:

```python
class HaltError(Exception):
    """An operational halt that is not a task failure — 🟡."""

class RateLimitError(HaltError):
    ...

class NetworkError(HaltError):
    ...

class PipelineStopError(Exception):
    """Raised to request a graceful halt of the pipeline."""
```

`HaltError`'s own docstring states its meaning precisely: "not a task failure." `docs/concepts/outcomes.md` defines halt (which `HaltError` represents) as **not a judgment about the work** — the task may be entirely fine. Escalation is the opposite: it **is** a judgment — an agent has concluded it cannot honestly proceed. Subclassing `HaltError` would bind escalation to the exact concept `docs/concepts/outcomes.md` separates it from. `PipelineStopError` is the correct sibling: also a direct `Exception` subclass, also caught explicitly (not via a shared base) in `main.py`'s `cli()`.

Today, none of `PlannerReviewer.plan()` (`:333-361`), `PlannerReviewer.review()` (`:363-406`), `PlanReviewer.review_plan()` (`:423-446`), or `Implementer.implement()` (`:464-491`) checks its own written artifact for anything beyond the existing `PLAN_REVIEW_PASS`/`REVIEW_PASS` signals (via `_has_signal`, `:42-43`) — `plan()` and `implement()` check nothing about their artifact's content at all. There is no way today for any of the four agent roles to signal "I cannot honestly proceed" in a way the harness acts on; `BLOCKED:` (pre-20.3) is prose only (confirmed: zero `BLOCKED` hits in `orchestrator/*.py`).

### The change

**1. New exception class**, declared beside `PipelineStopError` (`:113-114`), not beside `RateLimitError`/`NetworkError`:

```python
class EscalationError(Exception):
    """Raised when an agent cannot honestly produce its mandated output because
    the missing decision is outside its authority — escalation, not halt."""
```

A direct `Exception` subclass, deliberately **not** inheriting from `HaltError` — see rationale above; state it in the class docstring so a future reader does not "fix" it into the `HaltError` tree by analogy with `RateLimitError`/`NetworkError`.

**2. A detection helper** alongside `_has_signal` (`:42-43`), e.g. `_has_escalation(text: str) -> bool` reusing the same exact-line-in-last-5-lines check against the literal token `ESCALATION` (20.3's engine names this token) — or extend `_has_signal` itself to take the token as a parameter and call it with `"ESCALATION"`; either is acceptable as long as the check is the same shape as the existing PASS-signal check (last 5 non-blank-trimmed lines, exact match).

**3. Per-method wiring**, added at the end of each of the four methods, after the artifact is written and before any existing return:
- `PlannerReviewer.plan()` (`:333-361`): after the `_run_claude` call and before `_write_session(plan_path, "planner", ...)` (`:361`) returns control to the caller, check `plan_path`'s tail for `ESCALATION`.
- `PlannerReviewer.review()` (`:363-406`): after writing `review_path`, before the existing `_has_signal(review_path.read_text(), "REVIEW_PASS")` check (`:404`) — check for `ESCALATION` first; if present, do not fall through to the `REVIEW_PASS` check.
- `PlanReviewer.review_plan()` (`:423-446`): same shape, before the existing `_has_signal(review_path.read_text(), "PLAN_REVIEW_PASS")` check (`:444`).
- `Implementer.implement()` (`:464-491`): after the `_run_claude` call, check `plan_path`'s tail for `ESCALATION` (the implementer writes its escalation into the plan file it already owns, per 20.3's engine).

On a hit, in all four: write the sidecar via the existing `_write_session(plan_path, key, value)` helper — set `"step"` to `"escalated"` and a new field `"escalation"` to a small JSON-serializable summary (agent role, artifact path, a one-line excerpt of the missing decision pulled from the artifact's `## Escalation` section) — then `raise EscalationError(f"...")` quoting the artifact path and the one-line summary. Do not return `True`/`False` from `review_plan()`/`review()` in this case — the raise replaces the return entirely for this path, exactly as an uncaught exception already does for `NetworkError`/`RateLimitError` inside `_run_claude` today.

### Guards

- `EscalationError` is a **sibling** of `PipelineStopError`, never a `HaltError` subclass — this is the one guard this section must not get wrong; the class docstring states why.
- No call-site restructuring in `process_task` beyond section B's own branch below — every one of the four call sites calls these methods exactly as today; the exception propagates uncaught up through `process_task` → `cli()`, structurally identical to how `PipelineStopError` already propagates from deep inside `main.py`'s own loop today. `review_plan()`/`review()`'s existing `bool` return type is unchanged for the pass/fail case.
- `_write_session` is the only sidecar-writing mechanism used — per `.ai-factory/ARCHITECTURE.md`'s Key Principle #2 ("Sidecar is isolated — `_read_sessions`/`_write_session` live in `agents.py` only"), do not write the sidecar JSON file directly anywhere in this task.
- Do not touch `_classify_result` (`:76-97`) — that function classifies the raw Claude CLI process outcome (network/retry/ratelimit/error/ok) and is unrelated to this content-level artifact check.
- Do not touch `TestRunner` (`:493+`) — it has no LLM session, nothing to escalate.
- Do not subclass `HaltError` — this is the whole point of the sibling design above.
- Do not change `review_plan()`/`review()`'s return type from `bool` — the escalation path exits via exception, not via a third return value.
- Do not add an `except EscalationError` block anywhere in `agents.py` itself — it must propagate uncaught to `main.py`'s `cli()`, added in section C below.

### Verify

- `class EscalationError(Exception):` — confirm via `python -c "from orchestrator.agents import EscalationError, HaltError; assert not issubclass(EscalationError, HaltError)"`.
- Unit test (`tests/test_agents.py`): a plan/review/plan-review file ending with the `## Escalation` section + the `ESCALATION` marker causes the corresponding method to raise `EscalationError`, and the sidecar (`.json` sidecar of the plan path) ends up with `step == "escalated"` and a non-empty `escalation` field.
- Unit test: a file ending with `REVIEW_PASS`/`PLAN_REVIEW_PASS` (no `ESCALATION` line) behaves exactly as before — no regression to the existing pass-signal tests.

## B. Resume: `escalated` halts again instead of retrying

### Problem today

`resume.py`'s `_validate_sidecar_step` (`:11-62`) validates a **closed set** of sidecar `step` values — `planned:N`, `plan_review_failed:N`, `plan_reviewed`, `implemented:N`, `<fail_prefix>N` — documented explicitly in its own docstring (`:20-29`) and mirrored, per its own comment, by `task-rescue`'s closed-set table on the skills side. `"escalated"` (section A above) is not one of them: today, an unrecognized `step_value` falls through unchanged (`:61-62`, "unrecognized → return as-is; dispatch will fall through to heuristic"), and `_detect_step` (`:84-173`) has no branch for it either — it would fall through step 3 onward (`:143-173`), re-deriving a plan/implement/review state from disk heuristics and potentially **re-running the very step that just escalated**, silently losing the escalation.

`process_task` (`main.py:198-364`) has exactly one terminal-state branch today — `if step == "done":` (`:236-244`) — which marks the task done and commits. There is no equivalent branch for a step that must **not** be resumed normally but instead must re-halt, matching `docs/concepts/outcomes.md`'s invariant that escalation, like halt, is resumable: a run resumed before a human resolves the decision must halt again immediately, not silently retry.

### The change

**1. `resume.py:_validate_sidecar_step`** (`:11-62`). Add a branch recognizing `"escalated"` as always valid (mirroring the existing `planned:`/`implemented:` always-valid branch at `:32-37`, but with no `:N` suffix to parse — escalation is terminal, not iteration-indexed):

```python
if step_value == "escalated":
    return step_value
```

Placed before the `unrecognized → return as-is` fallback (`:61-62`), after the existing `plan_review_failed:`/`plan_reviewed`/`<fail_prefix>` branches. Update the function's docstring (`:20-29`) to document the new branch alongside the existing bullets.

**2. `resume.py:_detect_step`** (`:84-173`). After step 2's existing sidecar dispatch (`:120-141`), add an explicit branch for `step_value == "escalated"` returning a new terminal tuple, e.g. `("escalated", 0, plan_path)` — placed as its own `elif` inside the `if step_value:` block (`:126-141`), before the "unrecognized → fall through to heuristic" comment (`:141`), so an escalated sidecar never reaches the disk-heuristic steps 3-7 (`:143-173`).

**3. `main.py:process_task`** (`:198-364`). Add a new branch immediately alongside the existing `if step == "done":` one (`:236-244`):

```python
if step == "escalated":
    sessions = _read_sessions(plan_path)
    raise EscalationError(sessions.get("escalation", "(no escalation detail recorded)"))
```

Placed at the same point in the function as the `done` branch (right after `step, counter, plan_path = _detect_step(...)`, `:220-224`, and the `sessions`/`elapsed_offset` read at `:227-231` — reuse that same `sessions` read rather than re-reading). This mirrors the `done` branch's shape (a terminal state detected immediately after step-detection, handled before any agent is constructed) and makes a resumed-but-unresolved escalation fail loud and immediately rather than silently falling through to plan/implement/verify.

**4. `main.py`'s import line** (`:14`): add `EscalationError` to `from .agents import HaltError, Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, TestRunner, _read_sessions, _write_session`.

### Guards

- `"escalated"` carries **no** `:N` index — unlike `planned:N`/`implemented:N`, escalation is terminal (the run stops; there is no "next attempt" to count). Do not give it an ordinal suffix or a fail-tag pairing.
- Do not touch any other branch in `_validate_sidecar_step` or `_detect_step` — the existing five recognized forms (`planned:N`, `implemented:N`, `plan_review_failed:N`, `plan_reviewed`, `<fail_prefix>N`) and their validation/dispatch logic stay byte-identical.
- Do not add a `"escalated"` case to `_detect_task_step`/`_detect_test_task_step` (`:176-203`) directly — both are thin wrappers over `_detect_step`, which already carries the new branch; no wrapper-level change needed.
- Update the "closed set" language in whichever docstring/comment currently enumerates the five values (`resume.py`'s own docstrings, and the note in `_detect_step`'s docstring at `:91` listing "plan", "plan_review", "implement", `<verify_step>`, "done") to include `"escalated"` — do not leave a stale enumeration that omits it.
- This task does **not** touch `task-rescue`'s own mirrored table in the skills repo — that is the cross-repo follow-up noted in Phase 20's direction intro, not owned here.
- Do not make `"escalated"` resumable into a fresh attempt — that would silently discard the human decision requirement `docs/concepts/outcomes.md`/`docs/features/escalation.md` establish as the whole point of escalation.
- Do not touch `_plan_is_stale` (`:65-81`) — unrelated to sidecar step validation.

### Verify

- Unit test (`tests/test_main.py` or a new `tests/test_resume.py` case, matching wherever `_validate_sidecar_step`/`_detect_step` are currently tested): a sidecar with `"step": "escalated"` validates as `"escalated"` and `_detect_step` returns `("escalated", 0, plan_path)`.
- Unit test: `process_task`, given a plan path whose sidecar has `"step": "escalated"`, raises `EscalationError` without constructing any agent (`PlannerReviewer`/`Implementer`/`PlanReviewer` never instantiated for this path) and without calling `mark_done`/`_git_commit`.
- All pre-existing `_validate_sidecar_step`/`_detect_step` cases unchanged.

## C. Notification: a fourth alert tier

### Problem today

`notify.py:14-18` defines exactly two non-default alert tiers: `_FAIL_ALERTS = {"task-fail"}` (🔴) and `_HALT_ALERTS = {"stop"}` (🟡); `notify()`'s emoji selection (`:27`) is `"🔴" if alert_type in _FAIL_ALERTS else "🟡" if alert_type in _HALT_ALERTS else "🟢"` — anything not in either set defaults to 🟢 (success). An `"escalation"` alert type routed through this function unchanged would be painted green, i.e. reported as success, which is exactly backwards for an outcome that halts the run pending a human decision.

`main.py:cli()` (`:480-514`) has exactly two outcome-specific `except` arms today: `except PipelineStopError as e:` (`:501-507`, notifies `"task-fail"`) and `except HaltError as e:` (`:508-514`, notifies `"stop"`). Both are plain `except <ClassName>` blocks at the same nesting level, with no ordering dependency between them (verified: `grep -n "except HaltError" orchestrator/*.py` → exactly one hit, `main.py:508` — no other `except HaltError` exists anywhere in the package, so there is no most-specific-first ordering constraint to satisfy for a new sibling exception either). Without this section, `EscalationError` (section A) falls to the generic `except Exception` below both, which notifies `"stop"` and then re-raises — an unhandled-exception traceback, not a clean halt.

`orchestrator.json.example:11`'s `telegram_alerts_example_all` lists four tokens (`task-fail`, `stop`, `task`, `done`) and does not yet include `escalation`, so an operator following the example config has no way to subscribe to it.

### The change

**1. `notify.py`.** Add a third tier below `_HALT_ALERTS` (`:17-18`):

```python
# Alert types that report an escalation — a judgment the run cannot make on its own.
_ESCALATION_ALERTS = {"escalation"}
```

Extend `notify()`'s emoji selection (`:27`) to a three-way chain plus the green default, e.g.:

```python
emoji = (
    "🔴" if alert_type in _FAIL_ALERTS
    else "🟡" if alert_type in _HALT_ALERTS
    else "🔵" if alert_type in _ESCALATION_ALERTS
    else "🟢"
)
```

(🔵 matches the colour already in the alert table in `docs/reference/configuration.md` — keep them in sync if either changes.)

**2. `main.py:cli()`.** Add a third `except` arm, structurally identical to the existing two (`:501-514`), placed after `except HaltError` (order is not load-bearing — `EscalationError` is a sibling of `Exception`, not of `HaltError`, so it cannot be shadowed by or shadow the `HaltError` arm; placed last only to keep the three arms in outcome-severity reading order):

```python
except EscalationError as e:
    print(f"\n{'='*60}")
    print(f"ESCALATED — {e}")
    print(f"{'='*60}")
    msg = str(e).splitlines()[0]
    notify(config, f"Orchestrator escalated: {project_dir.name}\n{msg}\n{_run_summary()}", "escalation")
    sys.exit(0)
```

`EscalationError` must already be imported (section B's import-line change at `main.py:14` covers this).

**3. `orchestrator.json.example:11`.** Extend `telegram_alerts_example_all` to `["task-fail", "stop", "escalation", "task", "done"]` — same list-literal style, escalation inserted between the operational tokens and the success tokens, matching `docs/reference/configuration.md`'s alert-table row order.

### Guards

- No ordering hazard to enforce between `except EscalationError` and `except HaltError` — `EscalationError` is a plain `Exception` subclass (section A), not a `HaltError` subclass; either arm order is functionally correct. Keep them in the severity-reading order shown above for human readability only, not correctness.
- Do not touch `orchestrator.json` itself (gitignored, per-user; only `.example` is source-controlled).
- Do not touch `_FAIL_ALERTS`/`_HALT_ALERTS`'s existing membership (`{"task-fail"}`, `{"stop"}`) — only a new third set is added.
- Do not touch the `"task"`/`"done"` success-tier tokens or their 🟢 default path.
- Do not touch `docs/reference/configuration.md` — its alert table already carries the `escalation` row; this section only makes the code match it.
- Do not add the `escalation` token to `orchestrator.json` (the gitignored, non-example file) — only `.example` is source-controlled and documented.
- Do not touch `_run_summary()` or any other part of `runtime.py` — this section is confined to `notify.py`, `main.py`'s `cli()`, and `orchestrator.json.example`.

### Verify

- `notify(config, "test", "escalation")` (with `telegram_alerts` including `"escalation"` and valid mock/stub credentials) sends with 🔵, not 🟢.
- Unit test (`tests/test_notify.py`, matching however the existing `_FAIL_ALERTS`/`_HALT_ALERTS` cases are tested today): `"escalation"` alert type resolves to the new emoji tier, not the green default.
- `main.py`'s `cli()`, given a run that raises `EscalationError`, prints `ESCALATED — ...`, calls `notify(..., "escalation")`, and exits `0` (matching the existing `PipelineStopError`/`HaltError` exit behavior — clean exit, resumable state already on disk per section B).
- `grep -n "escalation" orchestrator.json.example` — one entry, matching the chosen token exactly.

## What NOT to do

- Do not subclass `HaltError` for `EscalationError` — it is a sibling of `PipelineStopError`.
- Do not add an `except EscalationError` block inside `agents.py` — the exception must propagate uncaught to `main.py`'s `cli()` (section C).
- Do not make the `escalated` sidecar value indexed, and do not let a resumed escalated task fall through to the disk heuristic (section B).
- Do not add the `escalation` token to the gitignored `orchestrator.json` — only `.example`.
- Do not touch `docs/reference/configuration.md`'s alert table — the row already exists; this task only makes `notify.py` match it.
- `uv run pytest` green at the end, covering all three sections.
