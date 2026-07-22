## Plan Review Summary

**Plan:** 18.2.1 — Marker-index grammar contract: red tests for `planned:N`/`implemented:N`
**Files Reviewed:** plan + `tests/test_main.py`, `orchestrator/resume.py`, governing spec `specs/trickster77777/34-marker-index-grammar-red-tests.md`, roadmap line 80
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap linkage** — OK. Plan title maps to roadmap line 80 (`18.2.1`); the `Spec:` note resolves to `specs/trickster77777/34-marker-index-grammar-red-tests.md`, which the plan follows faithfully. The chain to the leaf (`resume.py`) was walked.
- **Scope discipline** — OK. Plan touches only `tests/test_main.py` (Tasks 1–4) plus a verification-only Task 5, matching the spec's "tests only — no `main.py`/`resume.py` change" constraint.
- **Architecture/Rules** — no boundary or convention conflict; the task mirrors the existing `*_failed:N` ordinal convention and adds no new marker grammar, per the roadmap's pinned contract.

### Critical Issues
None.

Ground-truth verification performed (every claim traced against actual code, not the spec's description):

1. **Line references all correct.** Validation targets `test_validate_planned_returns_planned` (66), `test_validate_implemented_returns_implemented` (72), malformed-pattern donor (102), `_dirs`/`_call` helpers (40–52), `test_validate_unknown_value_passthrough` (78). Dispatch targets `test_detect_task_step_sidecar_planned_returns_plan_review` (264), `..._implemented_returns_review` (277), test-mode `..._sidecar_implemented_returns_test_run` (642). `resume.py` anchors (57 passthrough tail, 122 `planned`, 129 `implemented`, 138–139 first-plan-review) all match the file exactly.

2. **Red/green partition is exactly right** — traced through `_validate_sidecar_step` and `_detect_step`:
   - Validation `planned:2`/`implemented:2` → fall through the `return step_value` tail (line 57) unchanged ⇒ **GREEN**, as claimed.
   - Validation `planned:abc`/`implemented:abc` → no branch parses them, tail returns them unchanged (not `""`) ⇒ assertion `== ""` **fails = RED**, as claimed.
   - Dispatch `implemented:3`/`implemented:1` → `implemented:N` is unrecognized by the truthy-step block (only bare `implemented` matches line 129), falls to the heuristic; with the empty-plan-review `_dms_dirs` fixture, line 138–139 returns `("plan_review", 1)` — a *step* mismatch vs asserted `review` ⇒ **RED**, as claimed.
   - Dispatch `planned:2` → same heuristic path returns `("plan_review", 1)` — *counter* mismatch vs asserted `2` ⇒ **RED**, as claimed.
   - Dispatch `planned:1` → heuristic returns `("plan_review", 1)` == asserted ⇒ **GREEN** coincident pin, as claimed.
   - Test-mode `implemented:2` → heuristic returns `("plan_review", 1)` — *step* mismatch vs asserted `test_run` ⇒ **RED**, as claimed.

3. **No collateral regression.** The untouched bare-marker tests (adoption-gate tests at 508/531/558, test-mode planned at 673, subdir'd-dirs at 1128) stay green because 18.2.1 does **not** empty the bare always-valid tuple — that is 18.2.2's job. The plan correctly leaves them and does not over-flip.

4. **Coverage-loss of the bare-marker valid path is intentional**, not an oversight — the spec explicitly directs repointing lines 66/72 off the bare forms, and bare `planned`/`implemented` dispatch remains indirectly covered.

### Positive Notes
- The plan grounds its red/green claims in the actual `resume.py` control flow (naming the exact line the fallthrough resolves at), rather than restating the spec — this is why the partition is correct where the spec's own parenthetical is loose (see Deferred).
- The Task 5 "confirm the intended red" step names the precise pass/fail set, giving the implementer an unambiguous acceptance oracle and guarding against the common TDD failure of treating *every* new `:N` case as red.
- Task dependencies (Tasks 2–4 depend on Task 1; Task 5 depends on 2–4) are sensible for a tests-only task, and the explicit "do not weaken red / do not force green" guardrails pre-empt the most likely implementer error.

## Deferred observations
- Affects: `specs/trickster77777/34-marker-index-grammar-red-tests.md` §"Dispatch" (line 15) — The spec's parenthetical for `implemented:3` says today's heuristic yields `("implement", …)`, but against the empty-plan-review test fixture the heuristic actually returns `("plan_review", 1)` at `resume.py:138–139` (it never reaches the implement branch because no plan-review files exist). The plan correctly uses the ground-truth `("plan_review", 1)` result, so the deliverable is unaffected; this is only a minor imprecision in the governing spec's description, outside this task's `tests/test_main.py`-only file boundary. Worth tidying in the spec when it is next touched so a future reader isn't misled about the fallback tuple.

PLAN_REVIEW_PASS
