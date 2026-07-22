# Plan: 18.2.1 — Marker-index grammar contract: red tests for `planned:N`/`implemented:N`

## Context
Author the post-18.2 resume-dispatch grammar as tests-first assertions in `tests/test_main.py`, pinning the `planned:N`/`implemented:N` marker forms over the existing bare-marker suite. Tests only — no `main.py`/`resume.py` change; 18.2.2 makes the dispatch explicit.

**Red vs green — the spec's own split (do not collapse it).** Every pinned `(step, counter, plan_path)` tuple is the target grammar; some fail today (genuinely red — the point of TDD), some coincide with today's heuristic fallback and therefore **pass** today as forward-compatible regression guards. Per the governing spec (§12 "some assertions run red … some coincide with the current heuristic fallback"; §14 annotates only `implemented:3`/`planned:2` as red; §22–23 marks only the malformed `:N` validation as red today):

- **Genuinely red (must FAIL against today's code):** `implemented:3`, `implemented:1`, `planned:2` (implement dispatch); `implemented:2` (test-mode dispatch); `planned:abc`, `implemented:abc` (validation). These differ from today's result in *step* or *counter*.
- **Coincides / GREEN today (must PASS — a regression-guard pin, not red):** `planned:1` (dispatch — the heuristic returns `("plan_review", 1)` because the `_dms_dirs` fixture has no plan-review files, which equals the asserted tuple, and `N=1` collides with both the old hardcoded counter and the "first plan review" default); `planned:2` and `implemented:2` well-formed validation (both fall through today's passthrough tail at `resume.py:57` and return the input unchanged, which equals the assertion).

Do not weaken any genuinely-red assertion to green — that is 18.2.2's job. Do not "fix" a coincident-green case to be red — its passing is correct and it guards the grammar going forward.

## Settings
- Testing: yes (this task authors tests only)
- Logging: none
- Docs: no

## Tasks

### Phase 1: Repoint the `_validate_sidecar_step` grammar tests

- [x] **Task 1: Flip the bare validation tests onto the `:N` forms and add malformed-`:N` cases**
  Files: `tests/test_main.py`
  In the `_validate_sidecar_step` suite (lines ~60–105), repoint the two bare-marker tests onto the indexed grammar:
  - `test_validate_planned_returns_planned` (line 66): change the input/expected so `_call("planned:2", …)` asserts `== "planned:2"`; update the name to `test_validate_planned_n_returns_planned_n` and the docstring to describe the `planned:2` case.
  - `test_validate_implemented_returns_implemented` (line 72): change to `_call("implemented:2", …)` asserting `== "implemented:2"`; rename to `test_validate_implemented_n_returns_implemented_n` and update the docstring.
  Then add two new malformed-`:N` tests mirroring the existing `test_validate_plan_review_failed_malformed_n` pattern (line 102) — asserting the malformed index is cleared:
  - `_call("planned:abc", …)` asserts `== ""`.
  - `_call("implemented:abc", …)` asserts `== ""`.
  Use the existing `_dirs`/`_call` helpers (lines 40–52) exactly as the surrounding tests do. Do NOT touch `test_validate_unknown_value_passthrough` (line 78) — the generic heuristic-passthrough contract is unchanged.
  **Red/green:** the two well-formed flips (`planned:2`/`implemented:2` → unchanged) are **GREEN today** — they fall through today's passthrough tail at `resume.py:57` and return the input unchanged, which equals the assertion; they are forward-compatible regression pins, not red, so do NOT force them red. The two malformed cases (`planned:abc`/`implemented:abc` → `""`) are **genuinely RED today** — the passthrough at `resume.py:57` returns the string unchanged instead of clearing it; this redness is the TDD signal, do not weaken it (18.2.2 adds the `:N` branches that clear a malformed index).

### Phase 2: Repoint the `_detect_task_step` dispatch tests

- [x] **Task 2: Flip the implement-mode dispatch tests onto `implemented:N` → `("review", N)`** (depends on Task 1)
  Files: `tests/test_main.py`
  Repoint `test_detect_task_step_sidecar_implemented_returns_review` (line 277) off the bare `"implemented"` sidecar onto the indexed form, pinning the exact `(step, counter)` tuple the post-18.2 grammar must return:
  - `{"step": "implemented:3"}` → `_detect_task_step(...)` returns `step == "review"`, `counter == 3`, `returned_path == plan_path`.
  Add a second, sibling test for the `implemented:1` case → `("review", 1, plan_path)` (same body, different index) so both the load-bearing `N=3` and the boundary `N=1` are pinned. Follow the `_dms_dirs` fixture and sidecar-writing pattern of the existing test (lines 277–287): write the plan file, write `{"step": "implemented:N"}` to the `.json` sidecar, call `_detect_task_step`, assert the tuple.
  **Red/green:** both `implemented:3` and `implemented:1` are **genuinely RED today**. Today's dispatch (`resume.py:129`) matches only bare `"implemented"`; the `:N` form is unrecognized and falls to the heuristic — which, with the `_dms_dirs` fixture (no plan-review files), returns `("plan_review", 1)` at `resume.py:138–139`, a *step* mismatch against the asserted `review`. Do not weaken to green.

- [x] **Task 3: Flip the implement-mode dispatch tests onto `planned:N` → `("plan_review", N)`** (depends on Task 1)
  Files: `tests/test_main.py`
  Repoint `test_detect_task_step_sidecar_planned_returns_plan_review` (line 264) off the bare `"planned"` sidecar onto the indexed form:
  - `{"step": "planned:2"}` → `_detect_task_step(...)` returns `step == "plan_review"`, `counter == 2`, `returned_path == plan_path`.
  Add a second sibling test for `planned:1` → `("plan_review", 1, plan_path)`. Reuse the same `_dms_dirs` fixture and sidecar pattern as the existing test (lines 264–274).
  **Red/green:** the two cases split. `planned:2` is **genuinely RED today** — today's dispatch (`resume.py:122`) matches only bare `"planned"`; the `:N` form is unrecognized and falls to the heuristic, which (no plan-review files in the fixture) returns `("plan_review", 1)` at `resume.py:138–139`, a *counter* mismatch against the asserted `2`. `planned:1` is **GREEN today** — the same heuristic returns `("plan_review", 1)`, which equals the asserted tuple (`N=1` collides with the "first plan review" default), so this test **passes** today and is a forward-compatible regression pin, not red. Do NOT force `planned:1` red.

### Phase 3: Repoint the test-mode sibling

- [x] **Task 4: Flip the test-mode `_detect_test_task_step` implemented dispatch onto `implemented:N` → `("test_run", N)`** (depends on Task 1)
  Files: `tests/test_main.py`
  Repoint `test_detect_test_task_step_sidecar_implemented_returns_test_run` (line 642) off the bare `"implemented"` sidecar onto the indexed form, mirroring the implement-mode change so the `verify_step` sibling stays covered:
  - `{"step": "implemented:2"}` → `_detect_test_task_step(...)` returns `step == "test_run"`, `counter == 2`, `returned_path == plan_path`.
  Use the existing `_dtms_dirs` fixture and sidecar-writing pattern (lines 642–652). **Red/green:** `implemented:2` here is **genuinely RED today** — the heuristic (no plan-review files) returns `("plan_review", 1)`, a *step* mismatch against the asserted `test_run`. Do not weaken to green.

### Phase 4: Confirm the intended red

- [x] **Task 5: Run the suite and confirm the red set is exactly the genuinely-red cases** (depends on Task 2, Task 3, Task 4)
  Files: (none — verification only)
  Run `uv run pytest`. The pass/fail split must match the spec's own red-vs-green partition — do not treat every new `:N` case as red:
  - **Must FAIL (genuinely red):** the `implemented:3` and `implemented:1` implement-dispatch cases (Task 2), the `planned:2` implement-dispatch case (Task 3), the `implemented:2` test-mode dispatch case (Task 4), and the `planned:abc`/`implemented:abc` malformed validation cases (Task 1).
  - **Must PASS (coincident-green regression pins):** the `planned:1` implement-dispatch case (Task 3) and the `planned:2`/`implemented:2` well-formed validation cases (Task 1). A green here is correct, not a failure of the contract.
  Confirm no other suite regresses beyond the genuinely-red set above. Do NOT edit `main.py` or `resume.py` to turn the red cases green — that is task 18.2.2. This step only records that the pass/fail partition matches the grammar contract.
