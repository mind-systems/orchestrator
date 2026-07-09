# Review: Tests-first: complete the resume-dispatch matrix for both step-detectors — review 1

## Scope
Code changes are confined to `tests/test_main.py`: one helper (`_init_dirty_git_repo`) and 13 new characterization tests. No production code touched. Reviewed the diff, the surrounding test file, and the detector source (`_detect_milestone_step`, `_detect_test_milestone_step`, `_validate_sidecar_step` in `main.py`).

## Verification
- `uv run pytest tests/test_main.py` → **47 passed**. The suite is green on current code, as the plan requires (characterization, not red-first).
- Each new test maps to a distinct, previously-uncovered return branch, and the asserted `(step, counter, plan_path)` matches the source behaviour:
  - Milestone detector: `plan_review_failed:N`→`("plan", N+1)`; `plan_reviewed`→`("implement", 1)`; non-passing plan-review→`("plan", len+1)`; dirty-tree no reviews→`("review", 1)`; dirty-tree review not `REVIEW_PASS`→`("implement", len+1)`; dirty-tree review `REVIEW_PASS`→`("done", 0)` (the implement-mode `done` path, previously untested).
  - Test detector: `planned`→`("plan_review", 1)`; `plan_review_failed:N`→`("plan", N+1)`; no plan-reviews→`("plan_review", 1)`; non-passing plan-review→`("plan", len+1)`; clean tree→`("implement", 1)`; dirty-tree no test-runs→`("test_run", 1)`; dirty-tree test-run not `TEST_PASS`→`("implement", len+1)`.

## Correctness notes
- Sidecar-gated tests correctly write the artifact `_validate_sidecar_step` requires (the `plan-review-2.md` file for `plan_review_failed:2`, a `PLAN_REVIEW_PASS`-terminated file for `plan_reviewed`), so the sidecar branch fires rather than being cleared to the heuristic.
- The `len+1` counters (`plan_review_failed:2`→`3`, single non-passing review→`2`) are arithmetically consistent with the source.
- `_init_dirty_git_repo` dirties the tree with `src.py` **outside** `.ai-factory/`, which the detector's `:!.ai-factory` pathspec does not exclude — so the dirty-tree gate is genuinely exercised. The clean-tree test inlines its own git setup with no untracked file, correctly reaching the clean-tree branch.
- No existing test was restructured; the existing fixtures (`_dms_dirs`/`_dtms_dirs`) are reused as specified. Changes are purely additive.

## Findings
None. The tests are accurate green characterization of current detector behaviour and give the task-06 unification the full safety net the spec calls for.

REVIEW_PASS
