# Plan: Phase-persistent PlannerReviewer session

## Context
Carry the PlannerReviewer's `session_id` across consecutive milestones within the same roadmap section (`##`/`###` heading group) so the planner doesn't re-read DESCRIPTION.md, ARCHITECTURE.md, and spec notes from scratch on every milestone. The phase session is in-memory only — reset on any section change and dropped on process restart, with no disk persistence and no correctness impact.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Roadmap section tracking

- [x] **Task 1: Add `section` field to `Milestone`**
  Files: `orchestrator/roadmap.py`
  Add `section: str | None = None` to the `Milestone` dataclass (after `line_number`). Field holds the text of the nearest `##` or `###` heading above the milestone. Keep it last with a default so existing constructor call sites and the `slug` property are unaffected.

- [x] **Task 2: Track current section in `parse_roadmap()`**
  Files: `orchestrator/roadmap.py`
  Introduce a `current_section: str | None = None` variable in the scan loop. When a line (after `.strip()`) starts with `"## "` or `"### "`, set `current_section = stripped.lstrip("#").strip()`. When a `CHECKBOX_RE` match is appended, pass `section=current_section` to the `Milestone(...)` constructor. Do NOT reset the section on `---STOP---`, blank lines, or description continuation lines — only `##`/`###` headings change it. Note: heading tracking must run on every line regardless of the `marker_found` early-`continue` branch, so update `current_section` before that branch returns (place the heading check at the top of the loop body, ahead of the `if marker_found:` guard). Milestones after the `---STOP---` marker are not collected, so their section is irrelevant.

### Phase 2: Thread phase session through `process_milestone`

- [x] **Task 3: Accept `phase_session_id` and apply session priority in `process_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Add `phase_session_id: str | None = None` as the final parameter of `process_milestone()` and change the return type to `str | None`. Replace the existing session-init block (currently `if sessions: planner_reviewer.session_id = sessions.get("planner")`) with the priority logic: if the sidecar has a non-empty `planner` value use it; else if `phase_session_id` is provided use it; else leave `None`. The implementer session assignment (`implementer.session_id = sessions.get("implementer")`) is unchanged. Ensure every `return` path returns a session id for phase continuity:
    - `step == "done"` early return (planner not created): return the passed-in `phase_session_id`.
    - `mark_skipped(...)` early return (planner created and ran `plan()`): return `planner_reviewer.session_id`.
    - normal end of function: `return planner_reviewer.session_id`.

- [x] **Task 4: Accept `phase_session_id` and apply session priority in `process_test_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Mirror Task 3 in `process_test_milestone()`: add `phase_session_id: str | None = None` final parameter, change return type to `str | None`, apply the same sidecar-`planner`-first / `phase_session_id`-second / `None` priority, and return a session id on all paths (`done` early return → `phase_session_id`; `mark_skipped` early return → `planner_reviewer.session_id`; normal end → `planner_reviewer.session_id`).

### Phase 3: Inline loops with section tracking

- [x] **Task 5: Inline the loop in `_implement_loop()`** (depends on Task 3)
  Files: `orchestrator/main.py`
  Replace the `_run_loop(...)` call with an explicit `for` loop over `enumerate(pending, start=_next_number(plans_dir))`. Before the loop, init `current_section: str | None = None` and `phase_session_id: str | None = None`. Inside the loop: check `state.stop_requested` first (print the halt message and `break`, matching `_run_loop` behavior); when `milestone.section != current_section`, set `current_section = milestone.section` and reset `phase_session_id = None`; then call `phase_session_id = process_milestone(project_dir, milestone, i, max_iterations, planner_prompt_name, roadmap_filename, phase_session_id=phase_session_id)`.

- [x] **Task 6: Inline the loop in `_test_loop()`** (depends on Task 4)
  Files: `orchestrator/main.py`
  Mirror Task 5 in `_test_loop()`: replace the `_run_loop(...)` call with an explicit loop that tracks `current_section`/`phase_session_id`, resets `phase_session_id` to `None` on section change, checks `state.stop_requested` before each item, and threads `phase_session_id` through `process_test_milestone(project_dir, milestone, i, max_iterations, phase_session_id=phase_session_id)`. Leave `_run_loop` defined in the module (no longer called, kept for potential future use).

## Commit Plan
- **Commit 1** (after tasks 1-2): "Track nearest section heading on roadmap milestones"
- **Commit 2** (after tasks 3-6): "Thread phase-persistent planner session across milestones in a section"
