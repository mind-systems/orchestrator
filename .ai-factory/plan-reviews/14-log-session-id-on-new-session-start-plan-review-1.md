## Plan Review: Log session_id on new session start

**Files Reviewed:** 1 plan, 2 source files (agents.py, main.py)
**Risk Level:** Low

### Context Gates
- ARCHITECTURE.md: not present (WARN — non-blocking)
- RULES.md: not present (WARN — non-blocking)
- ROADMAP.md: milestone matches plan scope exactly, no drift

### Verification

**Task 1 — PlannerReviewer.plan() (line 185):** `plan()` does not pass `session_id` to `_run_claude()`, so every call creates a new session. The `is_new = self.session_id is None` pattern correctly detects the first session creation. On retries (main.py lines 220-223), `self.session_id` is already set, so retry sessions are not logged — this is consistent with the milestone spec ("first `_run_claude()` call that creates a new session").

**Task 2 — PlanReviewer.review_plan() (line 269):** Return value of `_run_claude()` is currently discarded. The plan correctly identifies this and proposes capturing it to log the session_id unconditionally. `PlanReviewer` has no `self.session_id` attribute, so every call is a fresh session. Correct.

**Task 3 — Implementer.implement() (line 323):** `implement()` passes `session_id=self.session_id`. First call has `None`, creating a new session (logged). Subsequent calls resume the existing session (not logged). Correct.

**Task 4 — RefactorPlanner.audit_and_plan() (line 370):** Same pattern as Task 1 — `audit_and_plan()` does not pass `session_id`, so each call creates a new session. The `is_new` check logs only the first one. Retry sessions (main.py lines 343-346) are not logged. Consistent with spec.

### Completeness check

- All four session-creating entry points are covered
- Methods that only resume sessions (`PlannerReviewer.review()`, `PlannerReviewer.patch()`, `RefactorPlanner.verify()`, `Implementer.implement()` on 2nd+ call) are correctly excluded
- File path (`orchestrator/agents.py`) is correct
- Line numbers match the current codebase
- No other files need changes — this is purely additive logging

### Positive Notes

- Clean, minimal scope — four small changes in one file
- Correct handling of the `PlanReviewer` special case (no persistent session_id)
- The `is_new` flag pattern avoids any race condition between checking and assigning `self.session_id`

PLAN_REVIEW_PASS
