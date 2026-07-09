# Plan: Tests-first: complete the resume-dispatch matrix for both step-detectors

## Context
Complete the unit-test matrix over `_detect_milestone_step` and `_detect_test_milestone_step` in `tests/test_main.py` — as green characterization of today's behaviour — so the task-06 detector unification has a full safety net. Every currently-uncovered return branch of both detectors gets one asserting test; no existing test is restructured.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Complete `_detect_milestone_step` matrix

- [x] **Task 1: Sidecar-driven dispatch branches (no git needed)**
  Files: `tests/test_main.py`
  Add two tests using the existing `_dms_dirs` fixture, placed alongside the current `_detect_milestone_step` sidecar tests (after `test_detect_milestone_step_sidecar_review_failed_returns_implement`, following the same write-plan-then-write-`.json`-sidecar pattern):
  - `plan_review_failed:N` dispatch → asserts `("plan", N+1, plan_path)`. Write plan file, sidecar `{"step": "plan_review_failed:2"}`, and the gating file `plan-reviews/01-slug-plan-review-2.md` (required so `_validate_sidecar_step` keeps the value); expect `("plan", 3, plan_path)`.
  - `plan_reviewed` dispatch → asserts `("implement", 1, plan_path)`. Write plan file, sidecar `{"step": "plan_reviewed"}`, and a passing `plan-reviews/01-slug-plan-review-1.md` ending in `PLAN_REVIEW_PASS` (required so validation keeps `plan_reviewed`); expect `("implement", 1, plan_path)`.

- [x] **Task 2: Heuristic non-git fall-through branch**
  Files: `tests/test_main.py`
  Add one test (no git repo needed — this branch returns before the `git diff`/`git status` calls) using `_dms_dirs`:
  - Latest plan-review not passing → asserts `("plan", len+1, plan_path)`. Write plan file, no sidecar, one `plan-reviews/01-slug-plan-review-1.md` whose content does **not** end in `PLAN_REVIEW_PASS`; expect `("plan", 2, plan_path)`.

- [x] **Task 3: Heuristic git-dependent branches (dirty-tree path)**
  Files: `tests/test_main.py`
  These branches run only after the passing-plan-review + dirty-tree gate. Add a small local helper (e.g. `_init_dirty_git_repo(tmp_path)`) near the `_dms_dirs` fixture that mirrors the existing git-init pattern from `test_detect_milestone_step_clean_tree_...` (`git init` + `--allow-empty` initial commit) and additionally writes an untracked file outside `.ai-factory/` (e.g. `src.py`) to dirty the tree. Then add three tests, each writing the plan file and a passing `plan-reviews/01-slug-plan-review-1.md`:
  - No review files → asserts `("review", 1, plan_path)`.
  - Latest review not `REVIEW_PASS` → write `reviews/01-slug-review-1.md` not ending in `REVIEW_PASS`; asserts `("implement", 2, plan_path)`.
  - All complete (implement-mode `done` path) → write `reviews/01-slug-review-1.md` ending in `REVIEW_PASS`; asserts `("done", 0, plan_path)`.

### Phase 2: Complete `_detect_test_milestone_step` matrix

- [x] **Task 4: Sidecar-driven dispatch branches (no git needed)**
  Files: `tests/test_main.py`
  Add two tests using the existing `_dtms_dirs` fixture, placed alongside the current `_detect_test_milestone_step` sidecar tests, following the same write-plan-then-write-sidecar pattern:
  - `planned` dispatch → asserts `("plan_review", 1, plan_path)`. Write plan file, sidecar `{"step": "planned"}` (no artifact gating needed — `planned` always validates); expect `("plan_review", 1, plan_path)`.
  - `plan_review_failed:N` dispatch → asserts `("plan", N+1, plan_path)`. Write plan file, sidecar `{"step": "plan_review_failed:2"}`, and gating file `plan-reviews/01-slug-plan-review-2.md`; expect `("plan", 3, plan_path)`.

- [x] **Task 5: Heuristic non-git fall-through branches**
  Files: `tests/test_main.py`
  Add two tests (no git needed — both return before the git calls) using `_dtms_dirs`:
  - No plan-review files → asserts `("plan_review", 1, plan_path)`. Write plan file, no sidecar, no plan-review files.
  - Latest plan-review not passing → asserts `("plan", len+1, plan_path)`. Write plan file, one `plan-reviews/01-slug-plan-review-1.md` not ending in `PLAN_REVIEW_PASS`; expect `("plan", 2, plan_path)`.

- [x] **Task 6: Heuristic git-dependent branches (clean- and dirty-tree paths)** (depends on Task 3)
  Files: `tests/test_main.py`
  Reuse the git-init pattern from Task 3 (clean commit for the clean-tree case; clean commit + untracked outside-`.ai-factory/` file for the dirty-tree cases). Add three tests, each writing the plan file and a passing `plan-reviews/01-slug-plan-review-1.md`:
  - Clean tree → asserts `("implement", 1, plan_path)`. `git init` + empty commit, no untracked files.
  - No test-run files (dirty tree) → asserts `("test_run", 1, plan_path)`. Dirty tree, no `test-runs/*.txt` files.
  - Latest test-run not `TEST_PASS` (dirty tree) → asserts `("implement", len+1, plan_path)`. Dirty tree, write `test-runs/01-slug-test-1.txt` not ending in `TEST_PASS`; expect `("implement", 2, plan_path)`.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Cover remaining _detect_milestone_step branches"
- **Commit 2** (after tasks 4-6): "Cover remaining _detect_test_milestone_step branches"
