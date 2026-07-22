# Marker-index grammar contract — red tests for `planned:N` / `implemented:N`

**Date:** 2026-07-22
**Source:** conversation context (TDD split of task 18.2 — the resume dispatch is a silent-failure state machine that already hid two bugs)

## Why this is a separate task

Task 18.2 indexes the two bare sidecar markers (`planned` → `planned:N`, `implemented` → `implemented:N`) so resume never re-runs a completed step. The surface it changes — `_validate_sidecar_step` / `_detect_step` in `resume.py` — is a **resume state machine**: a wrong marker→(step, counter) transition sends the orchestrator to the wrong phase/iteration **silently** (per the discriminator, a "test" surface; it is test-philosophy's own "state machine with wrong transition" example). This surface already hid **two** silent bugs (the lost verify counter and the redundant re-plan). Unlike 18.1 the functions already exist and are unit-tested, so there is **no skeleton** — this task writes the new grammar as a **tests-first contract** over the existing public surface, before the impl (18.2.2) makes it explicit. Authoring the target transitions first locks the grammar and forces 18.2.2 to satisfy the explicit branches, not lean on the disk heuristic.

## Deliverable (the grammar as tests, authored before the impl)

Add/flip assertions in `tests/test_main.py` (the `_validate_sidecar_step` / `_detect_task_step` suite) pinning the post-18.2 grammar. Some assertions run **red** against today's code, some coincide with the current heuristic fallback; all become explicit-branch-driven after 18.2.2. Do not weaken any to green — that is 18.2.2's job.

**Dispatch — `_detect_task_step` (the load-bearing, genuinely-red cases):**
- sidecar `implemented:3` → `("review", 3, plan_path)`  *(today: unrecognized → heuristic → `("implement", …)`, red)*
- sidecar `implemented:1` → `("review", 1, plan_path)`
- sidecar `planned:2` → `("plan_review", 2, plan_path)`  *(today: unrecognized → heuristic, red)*
- sidecar `planned:1` → `("plan_review", 1, plan_path)`
- Flip the two existing tests that pin the **bare** grammar — `test_detect_task_step_sidecar_planned_returns_plan_review` (line 264, bare `planned` → `("plan_review",1)`) and `test_detect_task_step_sidecar_implemented_returns_review` (line 277, bare `implemented` → `("review",1)`) — to the `:N` forms above. This is Class-A drift (the source grammar changed by design), not a silent bug — safe to repoint.

**Validation — `_validate_sidecar_step`:**
- `planned:2` → `"planned:2"`, `implemented:2` → `"implemented:2"` (valid).
- `planned:abc` → `""`, `implemented:abc` → `""` (malformed `:N` cleared — **red today**: the current passthrough returns the string unchanged instead of clearing it).
- Repoint `test_validate_planned_returns_planned` (line 66) and `test_validate_implemented_returns_implemented` (line 72) off the bare forms onto the `:N` forms.

**Test-mode sibling** (`_detect_test_task_step`), if the suite parametrises `verify_step`: `implemented:2` → `("test_run", 2, …)`.

## Scope note

This task authors tests only — no `main.py` / `resume.py` change. Because it repoints existing green tests onto not-yet-implemented behavior, the suite is intentionally **red** between this task and 18.2.2; that red state is the TDD signal, not a regression. The impl task (18.2.2) is what turns it green and carries the one-time `repo-stats-herald` sidecar migration.

## Verify

- `uv run pytest` runs; the new/flipped `_detect_task_step` `:N` cases and the malformed-`:N` validation cases are **red**; no other suite regresses beyond these intended reds.
- Every assertion names the exact `(step, counter)` tuple the post-18.2 grammar must return — the contract 18.2.2 implements against.

## What NOT to do

- Do **not** edit `main.py` or `resume.py` — the source change is 18.2.2. Tests only.
- Do **not** weaken a red assertion to make the suite green — the redness is the point; 18.2.2 resolves it.
- Do **not** add tests for loud surfaces — the marker string-formatting in `main.py` (`f"planned:{n}"`) fails loudly if malformed and gets no test; only the silent dispatch/validation transitions are pinned.
- Touch `tests/test_main.py` only.
