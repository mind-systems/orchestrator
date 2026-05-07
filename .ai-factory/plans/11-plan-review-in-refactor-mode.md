# Plan: Plan review in refactor mode

## Context
Add a PlanReviewer phase to `process_refactor_milestone()` so refactor plans are validated for safety before implementation, using the same plan-review cycle already present in `process_milestone()`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Agent revision support

- [x] **Task 1: Add plan_review_path parameter to RefactorPlanner.audit_and_plan()**
  Files: `orchestrator/agents.py`
  Add an optional `plan_review_path: Path | None = None` parameter to `RefactorPlanner.audit_and_plan()`. When provided, switch to a revision prompt identical to the pattern in `PlannerReviewer.plan()` (lines 167-172): tell the agent its plan was reviewed, point it to the review file, and ask it to update the plan. When `plan_review_path` is `None`, keep the existing audit prompt unchanged. The method already uses `self.session_id` for `--resume`, so the revision call naturally continues the same session.

### Phase 2: Plan review loop in process_refactor_milestone

- [x] **Task 2: Add plan_reviews_dir setup to process_refactor_milestone()**
  Files: `orchestrator/main.py`
  In `process_refactor_milestone()`, add `plan_reviews_dir = ai_factory / "plan-reviews"` and `plan_reviews_dir.mkdir(parents=True, exist_ok=True)` alongside the existing directory setup (after line 256). This mirrors `process_milestone()` line 132/136.

- [x] **Task 3: Insert plan review cycle after audit_and_plan()** (depends on Task 1, Task 2)
  Files: `orchestrator/main.py`
  After the `audit_and_plan()` call in `process_refactor_milestone()`, insert a plan review loop identical to the one in `process_milestone()` (lines 179-208). Specifically:
  - Loop `for attempt in range(1, max_iterations + 1)`
  - Each iteration: create a fresh `PlanReviewer(project_dir)`, build `plan_review_path = plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{attempt}.md"`, call `plan_reviewer.review_plan(plan_path, plan_review_path)`
  - If passed: print confirmation, break
  - If failed and `attempt == max_iterations`: raise `PipelineStopError` with the last plan-review path and contents
  - If failed and not last attempt: print "plan has issues — revising plan...", call `refactor_planner.audit_and_plan()` with `plan_review_path=plan_review_path` (the new parameter from Task 1) — also pass `milestone.title`, `milestone.description`, `plan_path`

- [x] **Task 4: Add safety guard before implement loop** (depends on Task 3)
  Files: `orchestrator/main.py`
  After the plan review loop and before the implement→verify loop, add the same safety guard as `process_milestone()` (lines 203-208): glob for `{seq}-{milestone.slug}-plan-review-*.md` in `plan_reviews_dir`, check that the latest file ends with `PLAN_REVIEW_PASS`, and raise `PipelineStopError` if not. This prevents implementation if somehow the loop exits without a passing review.
