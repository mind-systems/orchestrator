## Plan Review Summary

**Plan:** Fix REVIEW_PASS gate in reviewer prompt
**Files Targeted:** 2 (`orchestrator/prompts/reviewer.md`, `orchestrator/agents.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **ARCHITECTURE.md:** WARN — file does not exist. No boundary violations possible with a 2-file prompt-only change.
- **RULES.md:** WARN — file does not exist.
- **ROADMAP.md:** ✅ Plan maps directly to the pending milestone "Fix REVIEW_PASS gate in reviewer prompt". Description and scope match exactly.

### Verification

All three tasks were verified against the current codebase:

- **Task 1** — Line numbers 103–107 of `reviewer.md` match the described REVIEW_PASS rules block. The replacement text is heading-agnostic, which directly addresses the root cause (reviewer inventing non-standard section names to bypass the gate).
- **Task 2** — Lines 96–97 of `reviewer.md` contain the `### Suggestions` section to be removed. Removing it eliminates the false "blocking vs nice-to-have" split that let findings slip through as non-blocking.
- **Task 3** — Line 203 of `agents.py` contains the reinforcement prompt `"If no critical issues found, end the review file with REVIEW_PASS on its own line.\n"`. The proposed replacement aligns the runtime reinforcement with the updated prompt wording.

Full codebase search for `REVIEW_PASS`, `critical issues`, and `suggestions` confirmed no other locations need updating:

- `RefactorPlanner.verify()` (agents.py:380) uses outcome-based wording ("all fixes are correctly implemented") — not vulnerable to the same bypass.
- `PlanReviewer.review_plan()` (agents.py:266) uses `PLAN_REVIEW_PASS` with plan-specific wording — not affected.
- `main.py:438` is a programmatic file-content check, not a prompt — unaffected.
- `refactor-planner.md` lines 89/93 use outcome-based REVIEW_PASS rules — not vulnerable.
- `reviewer.md:112` ("Explain the 'why' behind suggestions") is generic review style advice, not a gate reference — harmless after the template change.

### Positive Notes

- The plan correctly diagnoses the root cause: section-name-based gating creates a loophole where non-standard headings bypass the gate.
- The fix is minimal and surgical — three targeted edits across two files, no structural changes.
- All line number references are accurate against the current codebase.
- The plan correctly scopes the change to the code reviewer prompt and its reinforcement, without touching the refactor-planner or plan-reviewer flows that don't have the same vulnerability.

PLAN_REVIEW_PASS
