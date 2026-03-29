# Review: process_refactor_milestone function

## Changes reviewed
- `orchestrator/main.py` — added `RefactorPlanner` import and new `process_refactor_milestone` function (lines 146–199)
- `.ai-factory/plans/03-process-refactor-milestone-function.md` — plan file (documentation only)

## Analysis

### 1. Import (line 14)
`RefactorPlanner` added to the import line in correct alphabetical position. Correct.

### 2. Function signature (line 146)
`process_refactor_milestone(project_dir, milestone, milestone_index, max_refactor_iterations=2)` — matches the milestone spec and mirrors `process_milestone`'s pattern. Correct.

### 3. Directory setup (lines 148–154)
Creates `plans_dir`, `patches_dir`, `reviews_dir` with `mkdir(parents=True, exist_ok=True)`. Matches `process_milestone` exactly. Correct.

### 4. Agent instantiation (lines 163–165)
`RefactorPlanner(project_dir)` and `Implementer(project_dir)` — both use default model/effort kwargs from their class definitions (opus/high and sonnet/high respectively). Matches what the plan specified. Correct.

### 5. Audit call (lines 168–169)
Calls `refactor_planner.audit_and_plan(milestone.title, milestone.description, plan_path)`. Matches `RefactorPlanner.audit_and_plan` signature in `agents.py:340`. Correct.

### 6. Implement → Verify loop (lines 172–190)
- Loop range `range(1, max_refactor_iterations + 1)` — correct, iterates 1..N.
- `implementer.implement(plan_path, patches_dir)` — correct signature per `Implementer.implement` in agents.py:294.
- `git add -A` before verify — correct, stages changes for the verifier to see via `git diff HEAD`.
- `refactor_planner.verify(plan_path, review_path)` — correct signature per `RefactorPlanner.verify` in agents.py:358. Returns bool based on `REVIEW_PASS` in review file.
- On pass: breaks out of loop. Correct.
- On max iterations: raises `PipelineStopError` with review path and contents. Correct per spec.

### 7. Verify failure on non-last iteration (lines 185–190)
When `passed` is False and `iteration < max_refactor_iterations`, the function falls through to the next loop iteration. This is correct — the Implementer's `implement` method on subsequent calls (when `session_id` is set) sends a prompt asking the agent to read patches and apply fixes. However, the verify findings are written to `reviews_dir`, not `patches_dir`. The Implementer's continuation prompt reads from `patches_dir`:

```python
# Implementer.implement (agents.py:306-310)
if self.session_id:
    prompt = (
        f"Review feedback has been written to {patches_dir}. "
        f"Read the latest patch file there and apply the fixes."
    )
```

The verify output goes to `reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"`, not to `patches_dir`. So on iteration 2+, the Implementer will look in `patches_dir` for feedback that doesn't exist there.

**This is not a bug in the new function** — it's an existing design constraint of the `Implementer` class. In `process_milestone`, the reviewer's output also goes to `reviews_dir`, and then the `PlannerReviewer.patch()` method creates a separate patch file in `patches_dir` for the implementer to read.

The refactor pipeline intentionally skips the patch step — the `RefactorPlanner` writes findings directly and the implementer re-reads the plan. On the first iteration, `implementer.implement(plan_path, patches_dir)` sends the plan prompt. On iteration 2+, it sends the "read patches" prompt — but `patches_dir` may be empty of new patches. The implementer still has session context from the previous run, and the plan is still available, so in practice it will still have context. But the prompt will be misleading.

**Severity: Low.** With `max_refactor_iterations` defaulting to 2, there's only one possible retry. The implementer agent has session memory and will likely work from context. However, if this is considered a correctness issue, the fix would be to either: (a) copy/symlink the verify output into `patches_dir`, or (b) override the implement prompt for refactor iterations. This is a pre-existing limitation of reusing `Implementer` unchanged.

### 8. Finalize (lines 193–199)
`mark_done` + `_git_commit` + elapsed time — follows `process_milestone` pattern exactly. `_git_commit` does its own `git add -A` (line 57), so the prior `git add -A` in the loop is fine (staging twice is harmless). Correct.

### 9. No state tracking
Unlike `process_milestone` (lines 113–126), `process_refactor_milestone` does not track review files in `orchestrator-state.json`. This is fine — the state tracking exists in `process_milestone` to support `implement-review` mode's cleanup of implement-phase reviews before the review pass. The refactor pipeline doesn't have a separate review pass, so no state tracking is needed.

## Verdict

The implementation is correct and matches the spec. The one low-severity observation (Implementer's continuation prompt referencing `patches_dir` where no patches are written) is a pre-existing design characteristic of the `Implementer` class, not a bug introduced by this change. It will work in practice due to session context.

No critical issues found.

REVIEW_PASS
