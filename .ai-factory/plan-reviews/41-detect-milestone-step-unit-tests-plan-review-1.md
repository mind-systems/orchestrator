# Plan Review: `_detect_milestone_step` unit tests

**Plan:** `41-detect-milestone-step-unit-tests.md`
**Risk Level:** 🔴 High — two blocking issues

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): no boundary violations — adds a single test module to `tests/test_main.py`, consistent with the existing scaffold. WARN: none.
- **Rules** (`.ai-factory/RULES.md`): not present — WARN (optional file absent).
- **Roadmap** (`.ai-factory/ROADMAP.md` present): milestone is test work sourced from `ROADMAP_TESTS.md` per project convention; linkage is fine.
- **skill-context** (`aif-review/SKILL.md`): absent — no project overrides to apply.

## Critical Issues

### 1. Test Command will fail on every run — wrong working directory (`cd orchestrator`)
The plan's `## Test Command` is:
```
cd orchestrator && uv run pytest tests/test_main.py -k detect_milestone_step
```
But this repo has a **single** `pyproject.toml` and a **single** `tests/`, both at the **repo root** (`/Users/max/projects/orchestrator/`). The inner `orchestrator/` is the package dir (`main.py`, `agents.py`, …) and has **no** `tests/`. `uv run` executes in the current working directory (it does not cd to the project root), so `cd orchestrator` makes pytest look for `orchestrator/tests/test_main.py`, which does not exist.

Verified on disk:
```
$ find . -name pyproject.toml -not -path '*/.venv/*'   → ./pyproject.toml   (root only)
$ find . -type d -name tests   -not -path '*/.venv/*'  → ./tests           (root only)
$ ls orchestrator/tests                                 → No such file or directory
```
Verified by running:
```
$ cd orchestrator && uv run pytest tests/test_main.py -k detect_milestone_step
collected 0 items ; "no tests ran" ; exit=4          # file not found (usage error)
$ uv run pytest tests/test_main.py -k detect_milestone_step   # from repo root
collected 18 items / 18 deselected ; exit=0
```
This is a hard blocker: `TestRunner.run()` (`agents.py`) executes `## Test Command` via `shell=True, cwd=project_dir` (the repo root) and returns `passed = (returncode == 0)`. Exit 4 ⇒ `passed=False` on every iteration ⇒ the milestone loops to `max_iterations` and **never passes**, no matter how correct the tests are. (The root `conftest.py` rescue only maps exit **5** → 0; this is exit 4, so it does not help.)

**Fix:** drop the `cd orchestrator` prefix:
```
uv run pytest tests/test_main.py -k detect_milestone_step
```
(The project `CLAUDE.md` still documents `cd orchestrator && uv sync`, but that reflects an older layout — `pyproject.toml`/`tests/` now live at the root. Match the current tree, not the stale doc.)

### 2. Task 2 does not exercise the clean-working-tree branch it claims to (false coverage + inert git fixture)
Task 2 is titled *"Clean-working-tree branch (git fixture required)"* and maps case 3 to `main.py:203-204`. Those are **two different code paths**:

- `main.py:203-204` is the **sidecar dispatch** for `step == "plan_reviewed"`. With sidecar `step="plan_reviewed"` (and a passing plan-review file present, as `_validate_sidecar_step` at `main.py:138-143` requires), the function returns `("implement", 1, plan_path)` **immediately at line 204** and never reaches the git logic.
- The real **clean-working-tree** branch is `main.py:221-231` — the `git diff HEAD` / `git status --porcelain` subprocess calls. It is reached only when the sidecar step is empty/invalid, plan-review files exist, **and** the latest passes (line 218).

As written (sidecar `step="plan_reviewed"`), the test returns at line 204; the `git init`/`commit` fixture is **dead weight** and the test gives false confidence that lines 221-231 are covered. The assertion `("implement", 1)` passes for the wrong reason — the only git-dependent path (and the most complex branch in the function) stays untested.

**Fix — pick the intent and make it explicit:**
- To genuinely test the git clean-tree branch (lines 221-231): **omit the sidecar `step`** (no `.json`, or one without `"step"`). Then `_read_sessions` → `{}`, dispatch is skipped, the passing plan-review file `plan-reviews/01-slug-plan-review-1.md` (ending `PLAN_REVIEW_PASS`) satisfies line 218, and a clean tree (only `.ai-factory/` paths present, excluded by `:!.ai-factory`) drives line 230 → `("implement", 1)`. Here `project_dir=tmp_path` and the git fixture is genuinely required.
- If the intent is only the `"plan_reviewed"` dispatch (line 204): keep `step="plan_reviewed"`, but **remove the git fixture and the "clean working tree" framing** and retitle — git is irrelevant to that path.

The first option is recommended: it covers the genuinely git-dependent logic that most benefits from a test.

## Notes / Lower-priority

- **Verified-correct facts (no change needed):** signature `(project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir)` (`main.py:157-160`); sidecar = `plan_path.with_suffix('.json')` (`agents.py:48`); case 1 `plan` (188-189); case 2 `planned`→`plan_review,1` (198-199); case 4 `implemented`→`review,1` (205-206); case 5 `review_failed:1`→`implement,2` (207-209). The plan correctly notes case 5 requires `reviews/01-slug-review-1.md` to exist — `_validate_sidecar_step` (145-152) would otherwise clear the step and the assertion would be wrong.
- **Canonical resolution (Task 3):** correct. With only `plans/01-slug.md` on disk and caller passing `seq="02"`, the glob `*-slug.md` resolves `best_num=1` → `seq="01"`, `plan_path=01-slug.md`; no sidecar + no plan-review files falls through to `214-215` → `("plan_review", 1, 01-slug.md)`. The implementer should not also create `02-slug.md` (harmless — `01` still wins — but cleaner to omit).
- **Function naming vs. `-k`:** `-k detect_milestone_step` only selects tests whose names contain `detect_milestone_step`. The plan describes cases but never tells the implementer to name functions `test_detect_milestone_step_*` (existing tests use `test_validate_*`). Add that instruction so the command actually collects them.
- **Case 2 qualifier is irrelevant:** "no plan-review files exist" doesn't affect the outcome — `"planned"` returns at 198-199 regardless. Harmless but misleading; consider dropping it.
- **Uncovered branches (informational, not blocking):** `218-219` (failed plan-review → re-plan), `235-236` (no review files → review), `239-240` (failed review → re-implement), `243` (`done`) aren't covered by any task. Acceptable for this scoped milestone — worth one sentence in the plan so the gap is intentional.
- **`project_dir` for Task 1:** cases 1/2/4/5 return before the git subprocess, so `project_dir=tmp_path` with no repo is fine and "no git needed" is accurate.

## Positive Notes
- Every `main.py` line reference for the sidecar dispatch is accurate, and the resume semantics (counter = n+1, artifact-existence requirements) are correctly understood.
- Task 3 targets the subtle canonical-path resolution and correctly asserts on the returned `Path`, not just the step tuple.
- Using `tmp_path` with real on-disk artifacts (rather than mocks) matches the existing `test_main.py` style and the orchestrator's file-based design.

## Verdict
Two concrete blocking issues: (1) the Test Command's `cd orchestrator` makes pytest exit 4 so the milestone can never pass, and (2) Task 2 tests the sidecar dispatch (line 204) with an inert git fixture instead of the clean-working-tree branch (221-231) it claims to cover. Fix #1 and #2, then resubmit.
