# Test Plan: `_validate_sidecar_step` unit tests

## Context
`_validate_sidecar_step` (`main.py:108`) decides whether a persisted resume-step value still points at a real artifact on disk, returning the value when valid or `""` when stale/malformed so the caller falls back to the disk heuristic. These tests pin its exact branch behavior using implement-mode arguments.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/ -v`

## Target Spec File
`tests/test_main.py`

## Notes for the implementer
- Import: `from orchestrator.main import _validate_sidecar_step`.
- The function does NOT read any sidecar/JSON — `step_value` is passed in directly. Only `plan_reviews_dir` and `artifact_dir` (reviews dir) are touched on disk.
- Use `tmp_path` for both directories. Helper constants for all cases: `seq="01"`, `slug="slug"`, `fail_prefix="review_failed:"`, `fail_suffix="-review-{n}.md"` (implement mode, from `main.py:195-196`).
- Create the two dirs (e.g. `plan_reviews_dir = tmp_path / "plan-reviews"`, `artifact_dir = tmp_path / "reviews"`, both `mkdir(parents=True)`) and only write the files a given case requires.
- Artifact (review) file path the function checks: `artifact_dir / f"{seq}-{slug}-review-{n}.md"` (`main.py:148`).
- Plan-review file path the function checks for `plan_review_failed:N`: `plan_reviews_dir / f"{seq}-{slug}-plan-review-{n}.md"` (`main.py:133`).
- For `plan_reviewed`: glob `{seq}-{slug}-plan-review-*.md` and a match requires file content whose `.strip().endswith("PLAN_REVIEW_PASS")` (`main.py:140-141`).
- Append `PLAN_REVIEW_PASS` as the last token of file content for the passing case; for the "no files" case, write nothing.

## Tasks

### Phase 1: Always-valid and empty inputs (no artifact reference)

- [x] **Task 1: Pass-through values that need no artifact**
  Files: `tests/test_main.py`
  Test cases:
  - `should return "" when step_value is "" (empty input short-circuits)` (case 1)
  - `should return "planned" when step_value is "planned"` (case 2)
  - `should return "implemented" when step_value is "implemented"` (case 3)
  - `should return "some_unknown_value" when step_value is unrecognized (pass-through to heuristic)` (case 11)

### Phase 2: `plan_review_failed:N` artifact validation

- [x] **Task 2: plan_review_failed:N gated on the plan-review file**
  Files: `tests/test_main.py`
  Test cases:
  - `should return "plan_review_failed:2" when plan-reviews/01-slug-plan-review-2.md exists` (case 4)
  - `should return "" when step_value is "plan_review_failed:2" but the plan-review file is missing` (case 5)
  - `should return "" when step_value is "plan_review_failed:abc" (malformed N raises ValueError)` (case 10)

### Phase 3: `plan_reviewed` PLAN_REVIEW_PASS check

- [x] **Task 3: plan_reviewed requires a passing plan-review file**
  Files: `tests/test_main.py`
  Test cases:
  - `should return "plan_reviewed" when a plan-review file content ends with PLAN_REVIEW_PASS` (case 6)
  - `should return "" when step_value is "plan_reviewed" but no plan-review files exist` (case 7)

### Phase 4: `<fail_prefix>N` (review_failed) artifact validation

- [x] **Task 4: review_failed:N gated on the review artifact file**
  Files: `tests/test_main.py`
  Test cases:
  - `should return "review_failed:1" when reviews/01-slug-review-1.md exists` (case 8)
  - `should return "" when step_value is "review_failed:1" but the review file is missing` (case 9)
