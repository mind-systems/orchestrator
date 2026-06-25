# Plan Review 2: `_detect_milestone_step` unit tests

**Plan:** `41-detect-milestone-step-unit-tests.md`
**Risk Level:** 🟢 Low — both prior blockers resolved, all facts verified against source

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): no boundary violations — adds tests to the existing `tests/test_main.py` module at the repo root, consistent with the scaffold. WARN: none.
- **Rules** (`.ai-factory/RULES.md`): not present — WARN (optional file absent).
- **Roadmap** (`.ai-factory/ROADMAP.md` present): test work sourced from `ROADMAP_TESTS.md` per project convention; linkage fine.
- **skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project overrides to apply.

## Resolution of Review 1 blockers

### Blocker 1 (Test Command `cd orchestrator`) — FIXED
`## Test Command` is now `uv run pytest tests/test_main.py -k detect_milestone_step` with no `cd orchestrator` prefix, and the plan adds an explicit note explaining that the single `pyproject.toml`/`tests/` live at the repo root and that the prefix would make pytest exit 4 (which `TestRunner.run()` treats as permanent failure). Correct: `uv run` executes in `cwd=project_dir` (the repo root). Resolved.

### Blocker 2 (Task 2 inert git fixture / false coverage) — FIXED
Task 2 now targets the genuine clean-working-tree branch (`main.py:221-231` → return at `230-231`), explicitly **omits the sidecar `step`** so `_read_sessions` → `{}` and the dispatch is skipped, supplies a passing `plan-reviews/01-slug-plan-review-1.md` to satisfy line 218, and keeps the tree clean so both `git diff HEAD -- . :!.ai-factory` and `git status --porcelain -- . :!.ai-factory` return empty. The git fixture (`git init` + `--allow-empty` commit with inline `user.email`/`user.name`) is now genuinely required. Resolved.

### Other Review 1 notes — addressed
- **Function naming:** new "Naming requirement" section instructs `test_detect_milestone_step_*` prefix so `-k detect_milestone_step` collects them (existing `test_validate_*`/`test_*_pattern_*` are correctly excluded). Verified existing tests would not collide.
- **Case 2 qualifier:** reworded to "returns at 199 regardless of any plan-review files" — no longer misleading.
- **Uncovered branches:** new "Coverage note" makes the 1–6 scope intentional and lists the out-of-scope branches (`218-219`, `235-236`, `239-240`, `243`).

## Fact verification against source (all confirmed)
- Signature `(project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir)` → `(step, counter, plan_path)` — `main.py:157-160`. ✓
- Sidecar = `plan_path.with_suffix('.json')`, `_read_sessions` returns `{}` when absent — `agents.py:47-54`; read at `main.py:192`. ✓
- Case 1 `plan` — `main.py:188-189`. ✓
- Case 2 `"planned"` → `("plan_review", 1)` — `main.py:198-199`, returns regardless of plan-review files. ✓
- Case 4 `"implemented"` → `("review", 1)` — `main.py:205-206`. ✓
- Case 5 `"review_failed:1"` → `("implement", 2)` — `main.py:207-209`. The required artifact is `reviews/01-slug-review-1.md`: `_validate_sidecar_step` is called with `artifact_dir=reviews_dir` and `fail_suffix="-review-{n}.md"` (`main.py:193-196`), and it clears the step if that file is missing (`main.py:145-152`). The plan's "review file must exist" requirement is correct. ✓
- Case 3 clean tree → `("implement", 1)` — `main.py:230-231`. ✓
- Case 6 canonical resolution: glob `*-{slug}.md` picks lowest seq → `seq="01"`, `plan_path=01-slug.md` (`main.py:171-185`); with no sidecar step and no plan-review files, falls through to `("plan_review", 1, 01-slug.md)` at `main.py:214-215`. Asserting on the returned `Path` (not the passed `02-slug.md`) is the right check. ✓

## Positive Notes
- The revised plan now traces every assertion to an exact line and pre-empts the two most likely implementer mistakes (wrong cwd, sidecar-vs-git-branch confusion) with inline rationale.
- Task 2's git fixture instructions correctly note that `user.email`/`user.name` are needed only for the commit, not for `diff`/`status` — accurate and saves the implementer a failed run.
- Using real on-disk artifacts under `tmp_path` matches the existing `test_main.py` style and the orchestrator's file-based design.
- Scope is honest: the Coverage note declares cases 1–6 and explicitly names the untested branches rather than implying full coverage.

## Verdict
Both blocking issues from Review 1 are resolved, every code reference checks out against `main.py`/`agents.py`, and the scope is clearly bounded. The plan is ready for implementation.

PLAN_REVIEW_PASS
