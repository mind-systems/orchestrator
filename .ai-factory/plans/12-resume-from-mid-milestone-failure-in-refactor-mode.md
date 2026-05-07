# Plan: Resume from mid-milestone failure in refactor mode

## Context
Add resume capability to `process_refactor_milestone()` so it detects where a previous run stopped and skips already-completed steps, reusing the existing `_detect_milestone_step()` helper and mapping its generic step names to the refactor flow.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Add resume logic to process_refactor_milestone

- [x] **Task 1: Call _detect_milestone_step and wire resume into process_refactor_milestone**
  Files: `orchestrator/main.py`

  Restructure `process_refactor_milestone()` to mirror the resume pattern already used in `process_milestone()` (lines 126-245). The changes:

  1. **Move agent creation after detection.** Currently agents are created at line 268-269 before any work. Move `RefactorPlanner` and `Implementer` instantiation to after the "done" early-return check (same pattern as `process_milestone` lines 160-161), so agents aren't created unnecessarily when all steps are complete.

  2. **Add step detection.** After computing `seq`, `plan_path`, and printing the milestone header, call `_detect_milestone_step(project_dir, seq, milestone.slug, plan_path, plan_reviews_dir, reviews_dir)` to get `(step, counter)`. Print the resume message if `step != "audit_and_plan"` (maps from `step != "plan"`).

  3. **Handle "done" step.** If `step == "done"`: call `mark_done` + `_git_commit`, print elapsed time, and return early — identical to `process_milestone` lines 151-157.

  4. **Conditionally run audit_and_plan.** Wrap the existing "Step 1: Audit + plan" block in `if step == "plan":`. When `counter > 1`, pass the previous plan-review file as `plan_review_path` (pattern: `{seq}-{slug}-plan-review-{counter - 1}.md`). After audit_and_plan completes, check `plan_path.exists()` — if missing, call `mark_skipped` and return (same guard as `process_milestone` lines 172-175). Set `step = "plan_review"` after successful audit.

  5. **Conditionally run plan review loop.** Wrap the plan review `for` loop in `if step in ("plan", "plan_review"):`. Change `range(1, max_iterations + 1)` to `range(counter, max_iterations + 1)` so it resumes from the correct attempt number. Keep everything else in the loop identical (PlanReviewer creation, review call, PipelineStopError on max, revision call to `audit_and_plan` with `plan_review_path`).

  6. **Conditionally run implement/verify loop.** Compute `impl_start = counter if step in ("implement", "review") else 1`. Change the loop to `range(impl_start, max_iterations + 1)`. When `step == "review" and iteration == counter`, skip the `implementer.implement()` call and go straight to `verify()` — the implementation is already done, only the verify step is needed. Keep the rest of the loop body (git add, verify, patch bridging, PipelineStopError) unchanged.

  Step name mapping from `_detect_milestone_step` → refactor flow:
  - `"plan"` → `audit_and_plan` (first or revised audit)
  - `"plan_review"` → plan review phase
  - `"implement"` → implementer runs
  - `"review"` → `verify` (RefactorPlanner.verify)
  - `"done"` → mark done + commit
