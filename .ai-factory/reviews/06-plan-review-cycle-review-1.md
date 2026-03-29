## Code Review: 06-plan-review-cycle

**Files changed:** `orchestrator/agents.py`, `orchestrator/main.py`

---

### Task 1: PlanReviewer writes review to file

- `Write` added to `PlanReviewer.tools` — matches `PlannerReviewer` and `RefactorPlanner` pattern. Correct.
- `review_plan()` signature changed from `tuple[bool, str]` to `bool`, `review_path: Path` parameter added. Correct.
- Prompt updated: "Do NOT write to a file" → "Write your full review to: {review_path}". Correct.
- Sentinel changed from `REVIEW_PASS` to `PLAN_REVIEW_PASS` — disambiguates plan reviews from code reviews. Correct.
- `_run_claude()` return value discarded (no longer need output text). Correct — pass/fail now detected via file read, matching `PlannerReviewer.review()` and `RefactorPlanner.verify()` patterns.
- Fallback `return False` when `review_path` doesn't exist — safe; treats agent failure as "didn't pass". Consistent with existing agents.

### Task 2: Planner accepts review file path

- `feedback: str | None` replaced with `plan_review_path: Path | None = None`. Correct.
- Prompt tells planner to `Read the review at: {plan_review_path}` — planner has `Read` tool, so it can access the file. No content leaked into prompt. Correct.
- `plan()` still doesn't pass `session_id` to `_run_claude()` — each plan call starts a fresh session. This is pre-existing behavior, not introduced by this change. The plan file and review file carry all necessary context for revision. After the loop, `self.session_id` holds the session from the final `plan()` call, which the subsequent `review()` call resumes. Session lifecycle is correct.

### Task 3: Iterative plan review loop

- `plan_reviews_dir = ai_factory / "plan-reviews"` created and `mkdir`'d alongside existing dirs. Correct.
- Loop structure `for attempt in range(1, max_iterations + 1)` — matches plan spec. Correct.
- Fresh `PlanReviewer` each iteration — no session reuse, consistent with its stateless design. Correct.
- Review path naming `{seq}-{milestone.slug}-plan-review-{attempt}.md` — matches spec. Correct.
- Pass → print + break. Correct.
- Fail + last attempt → `raise PipelineStopError(...)` with review contents. Correct.
- Fail + not last → call `planner_reviewer.plan()` with `plan_review_path=plan_review_path` to revise, then loop continues. Correct.
- Progress printing `>>> REVIEWING PLAN (attempt {attempt})...` — present. Correct.

### Cross-cutting checks

- **No other callers broken:** `PlanReviewer.review_plan()` was only called from `process_milestone`. `PlannerReviewer.plan()` with the old `feedback` kwarg was only called from `process_milestone`. Both call sites updated. No dangling references.
- **Import statement:** `PlanReviewer` already imported in `main.py` line 14. No change needed.
- **`review_plan` function (main.py:219):** Completely unrelated — reviews code against plans using `PlannerReviewer.review()`, not `PlanReviewer.review_plan()`. Unaffected.
- **Sentinel collision:** `PLAN_REVIEW_PASS` for plan reviews vs `REVIEW_PASS` for code reviews. No overlap. The `_already_passed()` helper in `run_review()` (line 429) checks for `REVIEW_PASS` in code review files — won't accidentally match plan review files since they live in `plan-reviews/`, not `reviews/`. Clean separation.
- **Pattern consistency with `process_refactor_milestone`:** The new plan-review loop mirrors the verify loop structure. `PipelineStopError` on exhaustion matches the refactor pattern (line 204). Consistent.

### No issues found

The implementation correctly follows the plan, is consistent with existing codebase patterns, and introduces no new bugs or type mismatches. All three tasks are properly wired together.

REVIEW_PASS
