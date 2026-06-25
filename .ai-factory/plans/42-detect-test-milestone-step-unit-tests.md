# Test Plan: `_detect_test_milestone_step` unit tests

## Context
`_detect_test_milestone_step` (`orchestrator/main.py:430`) resumes an interrupted *test-mode* milestone by inspecting the plan file, the JSON sidecar `step`, plan-review artifacts, the git working tree, and `test-runs/` artifacts, returning `(step, counter, plan_path)`. These tests pin its branch decisions for the five documented resume points.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_main.py`

## Target Spec File
`tests/test_main.py`

## Notes for the implementer (grounded in `main.py:430-500`)
- Import: `from orchestrator.main import _detect_test_milestone_step`.
- Signature: `_detect_test_milestone_step(project_dir, seq, slug, plan_path, plan_reviews_dir, test_runs_dir)`. There is **no** `reviews_dir` parameter — the artifact dir is `test-runs/`.
- Reuse the existing `_detect_milestone_step` setup style: build `.ai-factory/{plans,plan-reviews,test-runs}` under `tmp_path`, with `plan_path = plans/01-slug.md`. Mirror `_dms_dirs` but return the `test_runs_dir` (not `reviews_dir`).
- Sidecar is the `.json` file next to the plan: `plan_path.with_suffix(".json").write_text(json.dumps({"step": ...}))`.
- Sidecar validation (`main.py:456-459`) is called with `fail_prefix="test_run_failed:"` and `fail_suffix="-test-{n}.txt"`, gating `test_run_failed:N` on `test-runs/{seq}-{slug}-test-{N}.txt`. `plan_reviewed` is gated on a passing `plan-reviews/{seq}-{slug}-plan-review-*.md` (ends with `PLAN_REVIEW_PASS`).
- Test-run artifact glob (`main.py:493`): `test-runs/{seq}-{slug}-test-*.txt`; pass marker is the file ending with `TEST_PASS` (`main.py:497`).
- **Git is only required for cases that fall through the sidecar into the heuristic** (cases reaching `main.py:482-500`). Use the same git fixture as the existing clean-tree test: `git init` + `git -c user.email=... -c user.name=... commit --allow-empty -m init`.
- Clean working tree (no non-`.ai-factory` changes) returns `("implement", 1, plan_path)` (`main.py:490-491`) *before* the test-run files are inspected. To reach the test-run branches (cases requiring a `test-runs/*.txt` lookup via the heuristic), the working tree must be **dirty** for a path outside `.ai-factory/` — create a tracked-but-modified or untracked file under `tmp_path` (e.g. `tmp_path/src.py`) so `git status --porcelain -- . :!.ai-factory` is non-empty.
- Cases 2 and 4 are driven entirely by the sidecar and short-circuit before git (`main.py:460-472`), so they need no git repo.

## Tasks

### Phase 1: Sidecar-driven resume points (no git needed)

- [x] **Task 1: `_detect_test_milestone_step` — fresh start and sidecar steps**
  Files: `tests/test_main.py`
  Test cases:
  - `should return ("plan", 1, plan_path) when the plan file does not exist`
  - `should return ("implement", 1, plan_path) when sidecar step is "plan_reviewed" and a passing plan-review file is present`
  - `should return ("test_run", 1, plan_path) when sidecar step is "implemented"`
  - `should return ("implement", 2, plan_path) when sidecar step is "test_run_failed:1" and test-runs/01-slug-test-1.txt is present`

### Phase 2: Heuristic fall-through reaching the test-run artifacts (git fixture required)

- [x] **Task 2: `_detect_test_milestone_step` — done via latest passing test-run**
  Files: `tests/test_main.py`
  Test cases:
  - `should return ("done", 0, plan_path) when no sidecar step, a passing plan-review is present, the working tree is dirty, and the latest test-runs/01-slug-test-1.txt ends with TEST_PASS`
