## Review: Roadmap context in agent prompts

### Scope

Two files changed: `orchestrator/agents.py` (3 methods), `orchestrator/main.py` (2 functions).

### Verification

**agents.py — PlannerReviewer.plan() (line 166)**
- Parameters `roadmap_path: Path | None = None, line_number: int | None = None` added after `plan_review_path` — correct ordering, all call sites use keyword args.
- Guard uses `is not None` — correct (avoids falsy `0` trap noted in plan review).
- Roadmap line only injected in the first-call branch (`else`), not the revision branch — correct, revision resumes the same session.
- Produced prompt: `"Create an implementation plan for this milestone:\n\nRoadmap: ... (line N)\n**Title**\n..."` — clean formatting, no double newlines.

**agents.py — Implementer.implement() (line 299)**
- Restructured from "build first-call prompt then overwrite if session" to a clean `if/else`. Functionally equivalent — the old code wastefully built the first-call prompt even when overwriting it.
- Guard uses `is not None` — correct.
- Roadmap line only injected in the first-call branch (`else`), not the continuation branch — correct.
- Produced prompt: `"Roadmap: ... (line N)\nImplement the plan at: ..."` — clean.

**agents.py — RefactorPlanner.audit_and_plan() (line 350)**
- Parameters added. Guard uses `is not None` — correct.
- This method has no continuation branch (always first call) — `roadmap_line` is always computed, which is correct.
- Produced prompt: `"Audit the code area...\n\nRoadmap: ... (line N)\n**Title**\n..."` — clean.

**main.py — process_milestone() (line 79)**
- `roadmap_path` moved to line 91 (before agents). Old duplicate at the `mark_done` call and the `mark_skipped` early-return removed — both now use the single definition. Correct.
- `planner_reviewer.plan()` at line 105: passes `roadmap_path=roadmap_path, line_number=milestone.line_number`. Correct.
- Revision `plan()` call at lines 130-133: does NOT pass roadmap params — correct, session context already has it.
- `implementer.implement()` at line 141: passes both params. Correct.

**main.py — process_refactor_milestone() (line 168)**
- Same pattern: `roadmap_path` at line 178, old duplicate removed. Both `audit_and_plan()` (line 192) and `implement()` (line 197) pass params. Correct.

**main.py — review_plan() (line 227)**
- `implementer.implement(plan_path, patches_dir)` at line 267 does NOT pass roadmap params — correct, no milestone object available in this flow. Params default to `None`, roadmap line is empty string, no change in behavior.

### Type safety

- `milestone.line_number` is `int` (dataclass field in `roadmap.py`), matches `line_number: int | None`.
- `roadmap_path` is `Path`, matches `roadmap_path: Path | None`.
- `line_number + 1` is safe — guarded by `is not None` check.

### No issues found

Clean, minimal implementation. No bugs, no security concerns, no runtime risks.

REVIEW_PASS
