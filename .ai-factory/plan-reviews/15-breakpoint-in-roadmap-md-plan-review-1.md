## Plan Review: Breakpoint in ROADMAP.md

**Files Covered:** `orchestrator/roadmap.py`, `orchestrator/main.py`
**Risk Level:** Low

### Context Gates
- ARCHITECTURE.md: WARN — file not present, no boundary check possible.
- RULES.md: WARN — file not present, no convention check possible.
- ROADMAP.md: OK — plan matches milestone #15 exactly.

### Critical Issues

**1. `milestones_after_breakpoint` counts only non-done milestones — breaks M total calculation**

Task 1 says: "increment a counter each time `CHECKBOX_RE` matches a **non-done** milestone line after the breakpoint."

Task 2 then uses M = `len(milestones) + result.milestones_after_breakpoint` as the "total" in the log message.

`len(milestones)` includes ALL milestones before the breakpoint (done + pending), but `milestones_after_breakpoint` only includes pending ones after it. This means M understates the true total whenever done milestones exist after the breakpoint.

Example: 10 milestones before marker (8 done, 2 pending), 5 after marker (3 done, 2 pending). Plan gives M = 10 + 2 = 12, but the file has 15 milestones. The user sees "out of 12 total" which is wrong.

The milestone requirement says "how many milestones were left after it" — not "how many pending milestones." The counter should count ALL milestones (done + pending) after the breakpoint so M reflects the true file total. The "X milestones after marker not queued" phrasing works for either interpretation, but M must be accurate.

Fix: in Task 1, change the counting logic to increment the counter for every `CHECKBOX_RE` match after the breakpoint (drop the "non-done" filter). This makes M = total milestones in file and X = all milestones cut off by the marker.

### Positive Notes

- File paths, function names, and variable names all match the current codebase exactly.
- Correctly identifies both call sites of `parse_roadmap()` and leaves `run_review()` untouched (it reads `plans/` directly).
- The `ParseResult` dataclass approach is clean — callers destructure what they need, no API awkwardness.
- The `line.strip() == "---STOP---"` full-line match is the right level of strictness — won't false-positive on milestone descriptions.
- The `breakpoint_hit = marker_found AND milestones_after_breakpoint > 0` condition correctly handles the "marker at end of file" edge case from the requirement.
- Scope is tight — 3 tasks, 2 files, no unnecessary changes.
