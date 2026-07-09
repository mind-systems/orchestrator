## Plan Review Summary

**Plan:** Tests-first: complete the resume-dispatch matrix for both step-detectors
**Files Reviewed:** plan + `orchestrator/main.py` (`_validate_sidecar_step`, `_detect_milestone_step`, `_detect_test_milestone_step`), `tests/test_main.py`, spec `08-detector-matrix-tests.md`, `ROADMAP_TESTS.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** — `.ai-factory/ARCHITECTURE.md` present; test-only milestone touching `tests/test_main.py`, no boundary/dependency impact. PASS.
- **Rules** — no `.ai-factory/RULES.md`; no `.ai-factory/skill-context/aif-review/SKILL.md`. Nothing to enforce.
- **Roadmap** — traces cleanly to `ROADMAP_TESTS.md` (the two `_detect_*` unit-test lines) and governing spec `08-detector-matrix-tests.md`. The plan is the tests-first safety net that task 06 (`06-unify-milestone-pipeline.md`) must keep green. Linkage intact. PASS.

### Verification against source

Every branch the plan pins was checked against `main.py`, and every asserted `(step, counter)` and gating requirement matches:

`_detect_milestone_step`:
- Task 1A `plan_review_failed:2` → `("plan", 3)` — dispatch `n+1` (main.py:208-210); gating file `plan-reviews/01-slug-plan-review-2.md` correctly required by `_validate_sidecar_step` (main.py:138-145). ✓
- Task 1B `plan_reviewed` → `("implement", 1)` (main.py:211-212); passing plan-review needed for validation (main.py:146-152). ✓
- Task 2 latest plan-review not passing → `("plan", 2)`, returns *before* the git calls (main.py:226-227). ✓
- Task 3 dirty-tree branches: no review → `("review", 1)` (main.py:243-244); latest review not `REVIEW_PASS` → `("implement", 2)` (main.py:247-248); passing review → `("done", 0)` (main.py:251). Dirty-tree gate via untracked outside-`.ai-factory` file drives `git status --porcelain` non-empty (main.py:234-238). ✓

`_detect_test_milestone_step`:
- Task 4A `planned` → `("plan_review", 1)` (main.py:479-480), correctly no gating (always-valid at main.py:136). ✓
- Task 4B `plan_review_failed:2` → `("plan", 3)` (main.py:481-483). ✓
- Task 5A no plan-review → `("plan_review", 1)`; Task 5B latest not passing → `("plan", 2)` — both return before git calls (main.py:494-498). ✓
- Task 6A clean tree → `("implement", 1)` (main.py:508); Task 6B no test-run → `("test_run", 1)` (main.py:512-513); Task 6C latest test-run not `TEST_PASS` → `("implement", 2)` (main.py:515-518). ✓

Fixture reuse (`_dms_dirs`/`_dtms_dirs`), sidecar-as-`{stem}.json`, git-init-plus-empty-commit, and untracked-`src.py`-for-dirty patterns all match already-shipped green tests (e.g. `test_detect_milestone_step_clean_tree_...` proves `.ai-factory` exclusion holds even for the clean case). Counters, file-name patterns, and `PLAN_REVIEW_PASS`/`REVIEW_PASS`/`TEST_PASS` suffix gates are all faithful to the code.

**Matrix completeness:** with these six tasks the full return-branch matrix of both detectors is asserted. The one spec-listed dms branch the plan does *not* add a dedicated test for — heuristic "no plan-review files → `("plan_review", 1)`" — is already exercised by the existing `test_detect_milestone_step_canonical_path_resolution` (no sidecar, no plan-review files fall-through), so coverage is genuinely complete rather than missing. The plan correctly avoids a redundant duplicate.

### Critical Issues
None.

### Positive Notes
- Green-characterization framing is explicit and correct — every assertion holds on today's code, matching the spec's "not red-first" mandate.
- Branch-to-return mapping and counter arithmetic (`n+1`, `len+1`) are precise throughout.
- Correctly identifies which branches short-circuit before the `git diff`/`git status` calls (Tasks 2, 5) and which genuinely need a git tree (Tasks 3, 6), keeping fixtures minimal.
- Explicitly scopes out the processor loop / agent / commit surfaces per `test-philosophy` (loud, non-deterministic — not the detector's job).
- Commit plan cleanly splits by detector, mirroring the two roadmap lines.

PLAN_REVIEW_PASS
