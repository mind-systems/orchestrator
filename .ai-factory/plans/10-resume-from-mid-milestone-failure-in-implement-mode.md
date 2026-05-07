# Plan: Resume from mid-milestone failure in implement mode

## Context
Allow `process_milestone()` to detect where a previous run stopped and resume from that step, instead of always restarting from plan. A `_detect_milestone_step()` helper inspects existing artifact files and git state to determine the resume point and correct counter value.

**Session context on resume:** Agents are created fresh on each run — `PlannerReviewer` and `Implementer` have no `session_id` from the previous run. This is expected and acceptable: agents re-read artifact files (plans, patches, reviews) to reconstruct context. Do not attempt to restore or persist session IDs across runs.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Detection helper

- [x] **Task 1: Add `_detect_milestone_step()` helper function**
  Files: `orchestrator/main.py`
  Add a module-level helper function with this signature:
  ```python
  def _detect_milestone_step(
      project_dir: Path, seq: str, slug: str,
      plan_path: Path, plan_reviews_dir: Path, reviews_dir: Path,
  ) -> tuple[str, int]:
  ```
  Returns `(step, counter)` where `step` is one of `"plan"`, `"plan_review"`, `"implement"`, `"review"`, `"done"` and `counter` is the attempt/iteration number to use next.

  Detection chain (evaluate top-to-bottom, return on first match):
  1. `plan_path` does not exist → `("plan", 1)`
  2. No plan-review files matching `{seq}-{slug}-plan-review-*.md` in `plan_reviews_dir` → `("plan_review", 1)`
  3. Latest plan-review (sorted, last) does not end with `PLAN_REVIEW_PASS` → `("plan", N+1)` where N is the count of existing plan-review files for this slug (this is a revision — the counter represents the next attempt number)
  4. Working tree is clean — check using **both** `git diff HEAD` (tracked file changes) **and** `git status --porcelain` (untracked new files). Only return `("implement", 1)` when both commands produce empty output. Use `subprocess.run(..., cwd=project_dir, capture_output=True, text=True)` for each and check `stdout.strip()` on both.
  5. No review files matching `{seq}-{slug}-review-*.md` in `reviews_dir` → `("review", 1)`
  6. Latest review (sorted, last) does not end with `REVIEW_PASS` → `("implement", N+1)` where N is the count of existing review files for this slug
  7. Fallback (all steps appear complete — latest review has `REVIEW_PASS`): `("done", 0)` — caller should mark done and commit

  Place the function right above `process_milestone()` in `main.py`. Follow existing helper naming convention (`_` prefix, module-level).

### Phase 2: Integration

- [x] **Task 2: Wire `_detect_milestone_step()` into `process_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Call `_detect_milestone_step()` after creating directories and computing `seq`/`plan_path` but before creating agents. Restructure the function body based on the returned step:

  **Resume log line** — right after the detection call, if step is not `"plan"`, print:
  `>>> Resuming from step '{step}' (counter={counter})`

  **Handle `"done"` step** — if step is `"done"`, the previous run completed everything but crashed before mark_done/commit. Print elapsed time (record `milestone_start = time.monotonic()` before the detection call), then jump to `mark_done()` + `_git_commit()`, print the elapsed timing line, and return. Do not skip the timing print.

  **Plan step** — wrap the existing plan call in `if step == "plan":`. When `counter > 1` (revision), find the latest plan-review file (`{seq}-{slug}-plan-review-{counter - 1}.md`) and pass it as `plan_review_path` to `planner_reviewer.plan()`. When `counter == 1` (fresh), call `planner_reviewer.plan()` without `plan_review_path` (same as current code). Keep the existing `plan_path.exists()` guard + `mark_skipped` after the plan call. After the plan block, set `step = "plan_review"` and if `counter > 1` keep counter as-is, otherwise set `counter = 1`.

  **Plan review loop** — wrap in `if step in ("plan", "plan_review"):`. Change the `range()` start from `1` to `counter` so it resumes at the correct attempt number. The rest of the loop body stays the same (review → break on pass → raise on max → revise plan).

  **Plan review safety guard** — after the plan review loop and before the implement/review loop, add a defensive check: read the latest plan-review file for this slug from `plan_reviews_dir`, and verify it ends with `PLAN_REVIEW_PASS`. If it does not (or no plan-review file exists), raise `PipelineStopError`. This prevents the edge case where a resumed run with `counter > max_iterations` produces an empty plan review range — without this guard, an unreviewed plan would silently reach the implement loop.

  **Implement/review loop** — change the `range()` start from `1` to `counter` when step is `"implement"` or `"review"`, otherwise `1`. Inside the loop: when `step == "review"` and `iteration == counter` (first iteration of a resumed review), skip `implementer.implement()` and go straight to `planner_reviewer.review()`. On all other iterations, run both implement and review as before. The `orch_state` / `implement_reviews` tracking stays the same — it loads existing state and appends new review names.

  Keep all existing behavior (printing, PipelineStopError on max iterations, mark_done, git_commit, elapsed timing) intact.
