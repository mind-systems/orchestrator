## Code Review Summary

**Change under review:** `tests/test_main.py` only — repoint the `_validate_sidecar_step` / `_detect_task_step` / `_detect_test_task_step` suites onto the `planned:N`/`implemented:N` grammar (task 18.2.1). No `main.py`/`resume.py` change, as the plan and spec require.
**Files reviewed:** `tests/test_main.py` (in full), verified against `orchestrator/resume.py`, the plan, and governing spec `specs/trickster77777/34-marker-index-grammar-red-tests.md`.
**Risk level:** 🟢 Low

### Scope discipline
- Only `tests/test_main.py` is modified (the other diff entries are the plan/plan-review/sidecar artifacts, not code). `main.py`/`resume.py` untouched, matching the spec's "tests only" constraint and the plan's Task 5 prohibition. ✅

### Correctness — verified by running the suite
Ran `uv run pytest`. Result: **6 failed, 185 passed** — the failing set is *exactly* the plan's genuinely-red partition, and every coincident-green pin passes:

- **Genuinely red (fail today, as intended):**
  - `test_validate_planned_malformed_n_returns_empty` (`planned:abc` → `""`) — today's tail passthrough (`resume.py:57`) returns the string unchanged; RED. ✅
  - `test_validate_implemented_malformed_n_returns_empty` (`implemented:abc` → `""`) — same path; RED. ✅
  - `test_detect_task_step_sidecar_planned_2_returns_plan_review_2` (`planned:2` → counter 2) — heuristic yields `("plan_review", 1)`, counter mismatch; RED. ✅
  - `test_detect_task_step_sidecar_implemented_1_returns_review_1` (`implemented:1` → `review`) — heuristic yields `("plan_review", 1)`, step mismatch; RED. ✅
  - `test_detect_task_step_sidecar_implemented_3_returns_review_3` (`implemented:3` → `review`,3) — step+counter mismatch; RED. ✅
  - `test_detect_test_task_step_sidecar_implemented_2_returns_test_run_2` (`implemented:2` → `test_run`) — step mismatch; RED. ✅
- **Coincident-green regression pins (pass today, as intended):**
  - `test_validate_planned_n_returns_planned_n` (`planned:2` valid), `test_validate_implemented_n_returns_implemented_n` (`implemented:2` valid) — fall through `resume.py:57` unchanged; GREEN. ✅
  - `test_detect_task_step_sidecar_planned_1_returns_plan_review_1` (`planned:1` → `("plan_review", 1)`) — coincides with the heuristic default; GREEN. ✅

No test outside this partition regressed (185 pass, same as before minus the intentional reds). The bare-marker tests the plan-review flagged to leave untouched (adoption-gate at 508/531/558, test-mode `planned` at 673, subdir'd-dirs at 1128) remain and pass.

### Test quality
- Renames and docstrings are accurate to each new assertion (e.g. `..._planned_1_returns_plan_review_1`, docstring cites `planned:1`). No stale docstring left describing a bare marker.
- New tests reuse the existing `_dirs`/`_call`, `_dms_dirs`, `_dtms_dirs` fixtures and the sidecar-writing pattern verbatim — consistent with surrounding style.
- `test_validate_unknown_value_passthrough` correctly preserved — the generic heuristic-passthrough contract is unchanged.
- The pinned `(step, counter, plan_path)` tuples match the governing spec verbatim.

### Notes
- The intentional 6 failing tests are the TDD signal for 18.2.2, not a defect — the plan and spec both state the suite is red until 18.2.2 makes the dispatch explicit. A reviewer or CI gate that treats any red as blocking should be aware this task lands red by design.

No bugs, security issues, or correctness problems found. The change is exactly the tests-only grammar contract the plan specifies, and the observed pass/fail partition matches it precisely.

REVIEW_PASS
