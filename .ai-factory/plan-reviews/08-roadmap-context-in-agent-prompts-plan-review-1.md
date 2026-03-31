## Plan Review: Roadmap context in agent prompts

**Files referenced:** `orchestrator/agents.py`, `orchestrator/main.py`
**Risk Level:** 🟢 Low

### Verification

All line numbers and code structure assumptions checked against the current codebase:

- **Line 104** `planner_reviewer.plan(...)` — ✅ correct
- **Lines 130-133** revision `plan()` call — ✅ correct
- **Line 141** `implementer.implement(...)` — ✅ correct
- **Line 160** `roadmap_path` assignment in `process_milestone()` — ✅ correct
- **Line 192** `refactor_planner.audit_and_plan(...)` — ✅ correct
- **Line 197** `implementer.implement(...)` — ✅ correct
- **Line 219** `roadmap_path` assignment in `process_refactor_milestone()` — ✅ correct

Method signatures, branching logic (first-call vs revision in `plan()`, `self.session_id` check in `implement()`), and the `Milestone.line_number` field (0-based int, confirmed in `roadmap.py`) all match.

### Positive Notes

- Clean, minimal scope — only touches what's needed, no unnecessary refactoring.
- Correctly skips the revision branch in `plan()` and the continuation branch in `implement()` — those already have session context.
- Correctly identifies that `review_plan()` / `run_review()` don't need wiring — no milestone object available there.
- The `line_number + 1` conversion from 0-based to 1-based for the prompt is correct.

### Suggestion

The condition "only when both params are provided" should use explicit `is not None` checks rather than truthiness, since `line_number` is an `int` and `0` is falsy. In practice `line_number` will always be ≥ 5 for real roadmap files (headers precede milestones), so this is theoretical — but specifying `if roadmap_path is not None and line_number is not None:` in the plan removes any ambiguity for the implementer.

PLAN_REVIEW_PASS
