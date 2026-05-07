## Code Review: Plan review in refactor mode

**Files changed:** `orchestrator/agents.py`, `orchestrator/main.py`, `.ai-factory/plans/11-plan-review-in-refactor-mode.md`, `.ai-factory/plan-reviews/11-plan-review-in-refactor-mode-plan-review-1.md`

### agents.py — RefactorPlanner.audit_and_plan()

Verified the `plan_review_path` parameter addition at line 350. When truthy, the revision prompt mirrors `PlannerReviewer.plan()` exactly — self-contained, points the agent to both the plan file and the review file. When falsy, the original audit prompt is preserved unchanged (just re-indented).

Session handling is correct: `audit_and_plan()` never passes `session_id` to `_run_claude()`, so each call (initial or revision) starts a fresh session. `self.session_id` is updated each time, so the subsequent `verify()` call resumes from the latest audit/revision session. This matches how `PlannerReviewer.plan()` works.

### main.py — process_refactor_milestone()

**Directory setup (lines 254, 258):** `plan_reviews_dir` added alongside existing directories. Correct.

**Plan review loop (lines 276-297):** Structurally identical to `process_milestone()` lines 179-201, with two intentional differences:
1. Loop starts from `range(1, ...)` instead of `range(counter, ...)` — correct, since refactor mode has no resume support yet (that's milestone 12).
2. Revision calls `refactor_planner.audit_and_plan()` instead of `planner_reviewer.plan()` — correct agent for refactor mode.

Fresh `PlanReviewer` per attempt, `PipelineStopError` on exhaustion, correct file naming pattern — all match.

**Safety guard (lines 299-304):** Identical to `process_milestone()` lines 203-208. Correct glob pattern, correct `PLAN_REVIEW_PASS` check.

**Revision call (lines 292-297):** Passes `milestone.title`, `milestone.description`, `plan_path` (required positional args) and `plan_review_path` (keyword). The `roadmap_path` and `line_number` default to `None`, which is fine — the revision branch doesn't use them.

**Import:** `PlanReviewer` already imported at line 14. No changes needed.

### Downstream impact

The `verify()` call after the implement loop (line 315) resumes from `self.session_id`, which now points to whichever `audit_and_plan()` call was most recent (initial or revision). This is correct — the verifier gets context from the latest plan version.

The next milestone (12, "Resume from mid-milestone failure in refactor mode") explicitly depends on this plan review phase. The current implementation doesn't break that future work — it adds `plan_reviews_dir` and the review loop in a straightforward location that the resume logic can wrap around.

### Critical Issues

(none)

REVIEW_PASS
