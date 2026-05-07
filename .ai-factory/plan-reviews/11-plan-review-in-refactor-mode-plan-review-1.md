## Plan Review: Plan review in refactor mode

**Files Reviewed:** 3 (plan + agents.py + main.py)
**Risk Level:** 🟢 Low

### Context Gates
- **ARCHITECTURE.md:** WARN — file not present, cannot check boundary alignment.
- **RULES.md:** WARN — file not present, cannot check convention violations.
- **ROADMAP.md:** Milestone 11 ("Plan review in refactor mode") matches the plan's stated intent exactly. The next milestone (12, "Resume from mid-milestone failure in refactor mode") explicitly depends on "the plan review phase added above" — this plan correctly provides that prerequisite.

### Approach Verification

The plan mirrors the proven plan-review cycle from `process_milestone()` (main.py lines 179-208) and applies it to `process_refactor_milestone()`. The four tasks are correctly ordered with explicit dependencies.

Verified against codebase:
- **Task 1 (agents.py):** `RefactorPlanner.audit_and_plan()` signature at line 350 currently lacks `plan_review_path`. Adding it with the same branching pattern as `PlannerReviewer.plan()` (lines 166-172) is correct. The instruction to keep the existing prompt unchanged when `plan_review_path is None` preserves current behavior.
- **Task 2 (main.py):** `process_refactor_milestone()` at line 248 sets up `plans_dir`, `patches_dir`, `reviews_dir` but not `plan_reviews_dir`. Adding it after line 256 is the correct insertion point, mirroring lines 132/136 of `process_milestone()`.
- **Task 3 (main.py):** Inserting the plan review loop between `audit_and_plan()` (line 272) and the implement loop (line 275) is the correct location. The loop structure (fresh `PlanReviewer` per attempt, `PipelineStopError` on exhaustion, revision via `audit_and_plan(plan_review_path=...)`) matches `process_milestone()` exactly.
- **Task 4 (main.py):** The safety guard pattern (glob + check last file for `PLAN_REVIEW_PASS`) from lines 203-208 is the correct defense-in-depth measure.
- **Imports:** `PlanReviewer` is already imported in main.py (line 14). No import changes needed.

### Minor Concern

**Task 1 — wrong claim about session handling:** The plan states "The method already uses `self.session_id` for `--resume`, so the revision call naturally continues the same session." This is factually incorrect — `audit_and_plan()` (line 363-370) does NOT pass `session_id` to `_run_claude()`. Each call starts a fresh session.

This does **not** cause a functional problem because:
1. The plan instructs to follow `PlannerReviewer.plan()`'s pattern, which also doesn't use `--resume` for revisions — it works via a self-contained revision prompt that points to the review file.
2. `self.session_id` is still saved by each `audit_and_plan()` call, so the subsequent `verify()` call correctly resumes the session from the latest audit.

The risk is that the implementer reads this sentence, assumes session resumption is already wired up, and doesn't verify — but since the actual instruction ("identical to the pattern in PlannerReviewer.plan()") produces correct code regardless, this is non-blocking.

### Positive Notes

- Clean 4-task decomposition with correct dependency chain.
- Explicit line number references to the existing `process_milestone()` pattern make the plan easy to implement by direct analogy.
- The safety guard (Task 4) is a good defense-in-depth addition that prevents implementation without a passing plan review even if the loop logic has a bug.
- Correctly scoped — no unnecessary changes to agents, prompts, or CLI.

PLAN_REVIEW_PASS
