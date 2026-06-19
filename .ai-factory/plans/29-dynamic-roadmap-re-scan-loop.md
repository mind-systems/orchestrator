# Plan: Dynamic roadmap re-scan loop

## Context
Make the implement/test loops re-parse `ROADMAP.md` before every milestone and always run the first unchecked one top-to-bottom, so milestones added or reordered mid-run are honored, with a safety guard against spinning forever on a milestone whose checkbox never flips.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Shared dynamic loop

- [x] **Task 1: Add `_run_dynamic_loop` helper**
  Files: `orchestrator/main.py`
  Add a new function `_run_dynamic_loop(project_dir: Path, roadmap_path: Path, config: OrchestratorConfig, process_fn) -> None` next to the existing loop functions (around the current `_test_loop` / `_implement_loop`, ~line 635). Behavior:
  - Resolve `plans_dir = project_dir / ".ai-factory" / "plans"` and `plans_dir.mkdir(parents=True, exist_ok=True)`. Read `phase_sessions_enabled = config.enable_phase_sessions`.
  - **Startup summary (printed once)**: call `parse_roadmap(roadmap_path)`, compute `pending = [m for m in result.milestones if not m.done]`. If empty → `print("All milestones are done!")` and `return`. If `result.breakpoint_hit` → print the "stopped at breakpoint" summary using `len(result.milestones) + result.milestones_after_breakpoint` as total; else print the plain "Found N pending … out of M total." summary. Mirror the exact wording already used in the current `_implement_loop` (lines 689–697).
  - Initialize `current_section: str | None = None`, `phase_session_id: str | None = None`, `last_signature: tuple[str, str] | None = None`.
  - **`while not state.stop_requested:`** loop body:
    - Re-parse: `result = parse_roadmap(roadmap_path)`; `pending = [m for m in result.milestones if not m.done]`. If empty → `break`.
    - `milestone = pending[0]` (first unchecked, top-to-bottom).
    - `signature = (milestone.title, milestone.description)`. If `signature == last_signature` → `raise PipelineStopError(...)` with a message explaining the milestone's checkbox is still unchecked after processing and the loop refuses to re-run it forever. Else set `last_signature = signature`.
    - `i = _next_number(plans_dir)` (recomputed each iteration).
    - `_check_usage_limits(config)`.
    - Section/phase-session reset: if `milestone.section != current_section` → `current_section = milestone.section; phase_session_id = None`; `elif not phase_sessions_enabled: phase_session_id = None`.
    - `phase_session_id = process_fn(milestone, i, phase_session_id)`.
  - After the loop: `if state.stop_requested: print("\n>>> Stop requested — halting.")`.

### Phase 2: Convert loops to wrappers

- [x] **Task 2: Rewrite `_implement_loop` and `_test_loop` as thin wrappers** (depends on Task 1)
  Files: `orchestrator/main.py`
  Replace the bodies of both functions (current `_test_loop` ~lines 635–674 and `_implement_loop` ~lines 677–716) so each only resolves `roadmap_path`, checks existence (keep the existing `print(...)` + `sys.exit(1)` on missing file, with the correct filename in the message), and delegates to `_run_dynamic_loop` passing a `process_fn` lambda:
  - `_implement_loop(project_dir, config, planner_prompt_name="planner", roadmap_filename="ROADMAP.md")` →
    `lambda m, i, sid: process_milestone(project_dir, m, i, config, planner_prompt_name, roadmap_filename, phase_session_id=sid)`
  - `_test_loop(project_dir, config)` with `roadmap_path = project_dir / ".ai-factory" / "ROADMAP_TESTS.md"` →
    `lambda m, i, sid: process_test_milestone(project_dir, m, i, config, phase_session_id=sid)`
  Delete the now-unused fixed `pending` list, the startup-summary printing, and the `for i, milestone in enumerate(pending, ...)` iteration from both functions (this logic now lives in `_run_dynamic_loop`). Keep `process_milestone` / `process_test_milestone` signatures unchanged. Leave `_run_loop` (line 70) in place — it is no longer used by these two loops but may have other callers.

## Notes
- Termination depends on each processed milestone flipping its own checkbox via `mark_done` / `mark_skipped`, plus the `last_signature` guard as a backstop (prerequisite: robust marking from note 14).
- Resume is unaffected: `_detect_milestone_step` / `_detect_test_milestone_step` resolve the canonical seq by globbing `*-{slug}.md`, so a higher `_next_number` value still reuses an existing lower-seq plan file.
- `---STOP---` handling is unchanged — `parse_roadmap` already excludes milestones after the marker.
