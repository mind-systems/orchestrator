## Plan Review: Breakpoint in ROADMAP.md (Round 2)

**Files Covered:** `orchestrator/roadmap.py`, `orchestrator/main.py`
**Risk Level:** Low

### Context Gates
- ARCHITECTURE.md: WARN — file not present, no boundary check possible.
- RULES.md: WARN — file not present, no convention check possible.
- ROADMAP.md: OK — plan matches milestone #15 exactly.

### Previous Review Status

The critical issue from round 1 (counter only counting non-done milestones, breaking the M total) has been fixed. Task 1 now explicitly says "count every line that matches `CHECKBOX_RE` — both done (`[x]`) and pending (`[ ]`)." The M calculation in Task 2 is now correct: `len(milestones)` (all before marker) + `milestones_after_breakpoint` (all after marker) = true file total.

### Critical Issues

None.

### Verification

- **All callers covered:** `parse_roadmap()` is called at exactly two sites — `_implement_loop()` (line 489) and `_refactor_loop()` (line 515). Tasks 2 and 3 cover both. `run_review()` reads `plans/` directly and is correctly excluded.
- **Return type change is safe:** No other module imports or calls `parse_roadmap()`. The type change from `list[Milestone]` to `ParseResult` has no unhandled consumers.
- **Edge cases handled:** Marker at EOF (no milestones after) produces `breakpoint_hit=False` via the AND condition — no special message, as the milestone requires. No marker at all leaves `marker_found=False` — normal behavior. Marker before all milestones yields empty `milestones` list, `pending=[]`, early return with "All milestones are done!" — sensible.
- **`mark_done`/`mark_skipped` unaffected:** These take `Milestone` objects with `line_number` set during parsing. Milestones before the marker retain correct line numbers.
- **File paths, function names, variable names all match the current codebase.**
- **Scope is appropriately tight:** 3 tasks, 2 files, no unnecessary changes.

### Positive Notes

- Clean fix of the round 1 issue — the counting logic is now unambiguous.
- `ParseResult` dataclass is a good pattern — backward-compatible-ish (callers just add `.milestones`), no API awkwardness.
- The parenthetical in the log message ("X milestones after marker not queued") gives users clear information about what was cut off.
- Correct decision to leave `run_review()` and `run_implement_review()` untouched — they don't parse the roadmap.

PLAN_REVIEW_PASS
