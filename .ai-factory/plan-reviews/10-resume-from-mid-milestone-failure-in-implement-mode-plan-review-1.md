## Plan Review: Resume from mid-milestone failure in implement mode

**Files Reviewed:** Plan + 4 source files (main.py, agents.py, roadmap.py, state.py)
**Risk Level:** 🟡 Medium

### Context Gates
- `ARCHITECTURE.md` — WARN: file does not exist. No boundary/dependency check possible.
- `RULES.md` — WARN: file does not exist.
- `ROADMAP.md` — Plan aligns with the pending milestone description. Detection logic matches the roadmap spec.

### Critical Issues

#### 1. Plan review counter can exceed max_iterations — bypasses plan review gate entirely

If the original run exhausts all plan review attempts (e.g. 3 failed plan-reviews → `PipelineStopError`), then on resume `_detect_milestone_step()` returns `("plan", N+1)` where N = max_iterations. After the plan revision, the plan review loop becomes `range(max_iterations + 1, max_iterations + 1)` — an empty range. The code falls through to the implement/review loop, executing against a plan that failed review 3 times.

Concrete trace with `max_iterations=3`:
1. Original run: plan-review-1 FAIL, revision, plan-review-2 FAIL, revision, plan-review-3 FAIL → PipelineStopError
2. User re-runs without deleting artifacts
3. Detection: 3 plan-review files, last one failed → `("plan", 4)`
4. Plan block: revises plan using plan-review-3
5. Plan review loop: `range(4, 4)` — empty, skipped
6. Implement loop: runs against an unreviewed plan

**Fix:** Add a guard after the plan review loop (or at the start of the implement loop): read the latest plan-review file and verify it ends with `PLAN_REVIEW_PASS`. If not, raise `PipelineStopError`. This is a 3-line defensive check that prevents the silent bypass.

#### 2. `git diff HEAD` does not detect untracked new files

Detection step 4 uses `git diff HEAD` to determine whether implementation has started. `git diff HEAD` only shows differences for tracked files (and staged new files). If the implementer created only new untracked files before crashing, `git diff HEAD` is empty and detection returns `("implement", 1)` — re-implementing from scratch, potentially creating duplicate files or conflicts.

**Fix:** Replace `git diff HEAD` with a two-part check: `git diff HEAD` for tracked file changes AND `git status --porcelain` for any working tree changes (including untracked files). Return `("implement", 1)` only if both are empty.

### Other Issues

#### 3. "done" step handler skips elapsed time print

Task 2 says `("done", 0)` should "jump straight to `mark_done()` + `_git_commit()` and return." But the plan also says "Keep all existing behavior (printing, ... elapsed timing) intact." The done handler returns before `milestone_start` is used for the elapsed time print. Either the done handler should also print elapsed time, or the plan should acknowledge skipping it.

#### 4. Session context loss on resume is unacknowledged

When resuming, agents are created fresh — `PlannerReviewer` and `Implementer` have no session_id from the previous run. The reviewer loses the planner's reasoning context; the implementer on iteration 2+ gets the fresh "Implement the plan" prompt instead of the "Apply fixes from patches" prompt. This is an inherent limitation of cross-process resume and is functionally acceptable (agents re-read artifact files), but the plan should note it so the implementer doesn't try to restore session IDs.

### Positive Notes

- The detection chain is well-ordered — each step logically depends on the previous one's absence, making it easy to reason about.
- File naming conventions (`{seq}-{slug}-plan-review-{n}.md`) are consistent with the existing codebase.
- The `("done", 0)` fallback correctly handles the crash-between-mark_done-and-git_commit scenario.
- The approach of using existing artifact files for state detection (instead of adding a new state file) is clean and debuggable.
- The plan correctly avoids modifying `_detect_milestone_step()` when the step transitions happen — all flow control stays in `process_milestone()`.
