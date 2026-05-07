# Plan: Breakpoint in ROADMAP.md

## Context
Add `---STOP---` marker support so the orchestrator stops collecting milestones at that point, giving users control over how many milestones are queued per run.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Parser

- [x] **Task 1: Add `---STOP---` detection to `parse_roadmap()` and return structured result**
  Files: `orchestrator/roadmap.py`
  Add a `ParseResult` dataclass with three fields: `milestones: list[Milestone]`, `breakpoint_hit: bool`, `milestones_after_breakpoint: int`. In `parse_roadmap()`, while iterating lines, check if `line.strip() == "---STOP---"`. When found, set a local `marker_found` flag and stop appending to the `milestones` list. After the marker, continue iterating the remaining lines and count every line that matches `CHECKBOX_RE` — both done (`[x]`) and pending (`[ ]`) — into `milestones_after_breakpoint`. This counter represents ALL milestones cut off by the marker, not just pending ones. Return a `ParseResult` instead of a plain list. The `breakpoint_hit` field is `True` only when `marker_found` is true AND `milestones_after_breakpoint > 0` (per the requirement: marker at end of file with nothing after it is treated as if it weren't there).

### Phase 2: Callers

- [x] **Task 2: Update `_implement_loop()` to handle `ParseResult` and print breakpoint message** (depends on Task 1)
  Files: `orchestrator/main.py`
  Change `milestones = parse_roadmap(roadmap_path)` to `result = parse_roadmap(roadmap_path)` and `milestones = result.milestones`. Update the import to include `ParseResult`. After computing `pending`, replace the existing log line with conditional logic: if `result.breakpoint_hit`, print `Found N pending milestones out of M total (stopped at breakpoint — X milestones after marker not queued).` where N=`len(pending)`, M=`len(milestones) + result.milestones_after_breakpoint` (this is the true total of all milestones in the file since `milestones` contains all done+pending before the marker and `milestones_after_breakpoint` counts all done+pending after it), X=`result.milestones_after_breakpoint`. Otherwise print the existing message unchanged.

- [x] **Task 3: Update `_refactor_loop()` to handle `ParseResult` and print breakpoint message** (depends on Task 1)
  Files: `orchestrator/main.py`
  Same change as Task 2 but in `_refactor_loop()`. Extract `result = parse_roadmap(roadmap_path)`, derive `milestones = result.milestones` and `pending`, and add the same conditional breakpoint log line. The logic is identical to `_implement_loop()`.
