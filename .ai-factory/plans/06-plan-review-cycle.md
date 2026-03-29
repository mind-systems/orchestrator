# Plan: Plan review cycle

## Context
Replace the single-pass plan review with an iterative loop (up to `ORCHESTRATOR_MAX_ITERATIONS`). PlanReviewer writes reviews to files; Planner reads those files to improve the plan. If the plan never passes, the pipeline stops with `PipelineStopError`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: File-based plan review output

- [x] **Task 1: PlanReviewer writes review to file instead of returning raw text**
  Files: `orchestrator/agents.py`
  Add `Write` to `PlanReviewer.tools` (currently `["Read", "Glob", "Grep", "Bash"]` — needs `Write` to match the pattern used by `PlannerReviewer` and `RefactorPlanner`). Change `PlanReviewer.review_plan()` signature from returning `tuple[bool, str]` to `bool`. Add a `review_path: Path` parameter. Update the prompt to instruct the agent to write its review to the given file path (instead of `Do NOT write to a file. Just output your review.`). Change the sentinel from `REVIEW_PASS` to `PLAN_REVIEW_PASS` — instruct the agent to end the file with `PLAN_REVIEW_PASS` if the plan is solid. Detect pass/fail by reading the written file (like `PlannerReviewer.review()` does), not from chat output.

- [x] **Task 2: Planner accepts a review file path instead of raw feedback text**
  Files: `orchestrator/agents.py`
  In `PlannerReviewer.plan()`, replace the `feedback: str | None` parameter with `plan_review_path: Path | None = None`. When `plan_review_path` is provided, prompt the planner to read the review file at that path and update the plan to address the issues. The planner must read the file itself — do not pass file contents in the prompt.

### Phase 2: Iterative plan review loop

- [x] **Task 3: Replace single-pass plan review with iteration loop in process_milestone**
  Files: `orchestrator/main.py`
  Replace the current "Step 1.5: Plan review" block (lines ~101-110) with a loop up to `max_iterations`:
  1. Create `plan_reviews_dir = ai_factory / "plan-reviews"` and ensure it exists (alongside `plans_dir`, `patches_dir`, `reviews_dir` at the top of the function).
  2. Loop `for attempt in range(1, max_iterations + 1)`:
     - Instantiate a fresh `PlanReviewer` each iteration (it already uses fresh sessions).
     - Build review path: `plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{attempt}.md"`.
     - Call `plan_reviewer.review_plan(plan_path, review_path)` — returns `bool`.
     - If passed: `print` and `break`.
     - If not passed and not the last iteration: call `planner_reviewer.plan(milestone.title, milestone.description, plan_path, plan_review_path=review_path)` to revise.
     - If not passed and last iteration: `raise PipelineStopError(...)` with a message that includes the last plan-review file path and its contents (read via `review_path.read_text()`).
  3. Print progress like `>>> REVIEWING PLAN (attempt {attempt})...` for each iteration.

## Commit Plan
- **Commit 1** (after tasks 1-2): "Make plan review file-based with PLAN_REVIEW_PASS sentinel"
- **Commit 2** (after task 3): "Add iterative plan review loop with PipelineStopError on failure"
