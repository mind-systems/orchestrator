## Code Review: Breakpoint in ROADMAP.md

**Files Changed:** `orchestrator/roadmap.py`, `orchestrator/main.py`

### Verification

- **`ParseResult` dataclass** (`roadmap.py:27-31`): Three fields match the plan. Placed correctly between `Milestone` and `parse_roadmap()`.

- **`parse_roadmap()` logic** (`roadmap.py:34-64`): Marker detection uses strict `line.strip() == "---STOP---"` — no false positives on markdown horizontal rules (`---`) or milestone descriptions. After the marker, the counter increments for every `CHECKBOX_RE` match regardless of done/pending status — correctly counts ALL milestones cut off. `breakpoint_hit` requires both `marker_found` and `milestones_after_breakpoint > 0`, handling the "marker at end of file" edge case per the requirement.

- **Both call sites updated**: `_implement_loop()` (line 489) and `_refactor_loop()` (line 520) both destructure `ParseResult` correctly. The `total` calculation `len(milestones) + result.milestones_after_breakpoint` produces the true file-wide milestone count since `milestones` contains all (done+pending) before the marker and `milestones_after_breakpoint` counts all (done+pending) after it.

- **No broken consumers**: `parse_roadmap()` is only called at those two sites. `run_review()` reads `plans/` directly. `mark_done()` and `mark_skipped()` take individual `Milestone` objects with `line_number` — unaffected since milestones before the marker retain their original line numbers.

- **Multiple markers**: A second `---STOP---` after the first is harmlessly ignored (doesn't match `CHECKBOX_RE`, already in the `marker_found` branch). Reasonable behavior.

- **`ParseResult` import** (`main.py:15`): Imported but not referenced by name in any annotation or expression — technically unused at runtime. Not a bug, and it makes the dependency explicit for readers. Acceptable.

### Critical Issues

None.

REVIEW_PASS
