# Plan: process_refactor_milestone function

## Context
Add the `process_refactor_milestone` function to `main.py` that drives the refactor pipeline: audit → implement → verify, with iteration limits and error handling matching existing patterns.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Wiring

- [x] **Task 1: Import RefactorPlanner in main.py**
  Files: `orchestrator/main.py`
  Add `RefactorPlanner` to the existing import from `.agents` on line 14. The import line currently reads:
  `from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError`
  Add `RefactorPlanner` to it (keep alphabetical order).

### Phase 2: Core function

- [x] **Task 2: Add process_refactor_milestone function** (depends on Task 1)
  Files: `orchestrator/main.py`
  Add `process_refactor_milestone(project_dir: Path, milestone, milestone_index: int, max_refactor_iterations: int = 2)` after the existing `process_milestone` function (after line 143). Follow the structure of `process_milestone` but with the refactor chain:

  1. **Setup** — create `plans_dir`, `reviews_dir` under `.ai-factory/`. Build `seq` as zero-padded milestone_index and `plan_path` from it (same pattern as `process_milestone` lines 73–81). Print milestone banner.
  2. **Agents** — instantiate `RefactorPlanner(project_dir)` and `Implementer(project_dir)`. Record `milestone_start` with `time.monotonic()`.
  3. **Audit** — call `refactor_planner.audit_and_plan(milestone.title, milestone.description, plan_path)`. Print `>>> AUDITING...` before the call.
  4. **Implement → Verify loop** — iterate from 1 to `max_refactor_iterations`:
     - Print `>>> IMPLEMENTING (iteration N)...` and call `implementer.implement(plan_path, patches_dir)`. Create `patches_dir` (`ai_factory / "patches"`) alongside the others in setup.
     - Stage all changes with `git add -A` (same as `process_milestone` line 121).
     - Build `review_path` as `reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"`.
     - Print `>>> VERIFYING (iteration N)...` and call `passed = refactor_planner.verify(plan_path, review_path)`.
     - If `passed` — print success message and break.
     - If not passed and this is the last iteration — read the review file contents and raise `PipelineStopError` with a message containing both the review file path and its contents. Format: `f"Max refactor iterations ({max_refactor_iterations}) reached.\n\nLast review: {review_path}\n\n{review_path.read_text()}"`.
  5. **Finalize** — after the loop (only reached on pass): call `mark_done(roadmap_path, milestone)` and `_git_commit(project_dir, milestone.title)`. Print elapsed time in `Nm Ns` format (same pattern as `process_milestone` lines 141–143).
