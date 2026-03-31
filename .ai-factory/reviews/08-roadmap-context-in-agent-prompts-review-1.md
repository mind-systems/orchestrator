## Code Review Summary

**Files Reviewed:** 2 (orchestrator/agents.py, orchestrator/main.py)
**Risk Level:** 🟢 Low

### Context Gates
- ARCHITECTURE.md: not present — WARN (no boundary rules to check against)
- RULES.md: not present — WARN (no explicit convention rules)
- ROADMAP.md: milestone 8 is marked `[x]` — matches committed work
- skill-context/aif-review/SKILL.md: not present — WARN

### Verification

**agents.py — PlannerReviewer.plan() (line 166)**
- New params `roadmap_path: Path | None = None, line_number: int | None = None` added correctly as keyword-only defaults.
- Guard `if roadmap_path is not None and line_number is not None` — avoids the falsy `line_number == 0` trap. Correct.
- Roadmap line injected only in the first-call branch (the `else`), not the revision branch. Correct — revision resumes the same session which already has context.

**agents.py — Implementer.implement() (line 299)**
- Restructured from "build prompt then overwrite if session" to a clean `if/else`. The old code wastefully built the first-call prompt even when overwriting it. Functionally equivalent, strictly better.
- Guard uses `is not None`. Correct.
- Roadmap line only in the first-call branch. Correct.

**agents.py — RefactorPlanner.audit_and_plan() (line 350)**
- Same param pattern. Guard uses `is not None`. Correct.
- No continuation branch (always first call), so `roadmap_line` is always computed. Correct.

**main.py — process_milestone() (line 79)**
- `roadmap_path` moved to line 91 (before agent creation). Old duplicates at `mark_done` and `mark_skipped` removed — both now use the single definition. Correct.
- First `plan()` call (line 105) passes both params. Correct.
- Revision `plan()` call (lines 130-133) does NOT pass roadmap params — correct, session already has context from first call.
- `implementer.implement()` (line 141) passes both params. Correct.

**main.py — process_refactor_milestone() (line 168)**
- Same pattern: `roadmap_path` at line 178, old duplicate removed. Both `audit_and_plan()` (line 192) and `implement()` (line 197) pass params. Correct.

**main.py — review_plan() (line 227)**
- `implementer.implement(plan_path, patches_dir)` at line 267 does NOT pass roadmap params — correct, this flow has no milestone object. Params default to `None`, `roadmap_line` becomes empty string. No behavior change.

### Type Safety
- `milestone.line_number` is `int` (dataclass field in `roadmap.py` line 17). Matches `line_number: int | None`.
- `roadmap_path` is `Path`. Matches `roadmap_path: Path | None`.
- `line_number + 1` is safe — guarded by `is not None` check.

### Critical Issues
None.

### Suggestions
None.

### Positive Notes
- Clean restructuring of `Implementer.implement()` — the if/else is clearer than the old "build then overwrite" pattern.
- Consistent guard pattern (`is not None`) across all three methods avoids the `line_number == 0` falsy trap.
- Minimal, surgical changes — only the methods that need roadmap context were touched.

REVIEW_PASS
