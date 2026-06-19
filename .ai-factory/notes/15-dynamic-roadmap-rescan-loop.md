# Dynamic roadmap re-scan loop — always run the first pending milestone top-to-bottom

**Date:** 2026-06-19
**Source:** conversation context

## Key Findings

- `_implement_loop` and `_test_loop` in `main.py` parse the roadmap **once** at startup, build a fixed `pending` list, and iterate it with `for i, milestone in enumerate(pending, start=_next_number(plans_dir))`.
- Consequences: a milestone added to the roadmap mid-run is never seen; a milestone inserted **above** already-processed ones is never picked; `line_number` is frozen at startup for every milestone even though the file is edited throughout the run.
- Desired behavior: re-parse the roadmap **before each milestone** and select `pending[0]` — the first unchecked milestone top-to-bottom. New or reordered tasks are honored on the next selection; execution is always strictly top-to-bottom.
- Termination is guaranteed because every processed milestone flips its own checkbox (`mark_done` or `mark_skipped`) or the pipeline raises `PipelineStopError`. The robust marking from note 14 is what makes this safe — without it a mis-mark would re-select the same milestone forever, so note 14 is a prerequisite.

## Details

### Current state (`orchestrator/main.py`)

Both loops share this shape (`_implement_loop` ~line 677, `_test_loop` ~line 635):

```python
result = parse_roadmap(roadmap_path)
pending = [m for m in result.milestones if not m.done]
...
current_section, phase_session_id = None, None
for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
    if state.stop_requested: break
    _check_usage_limits(config)
    if milestone.section != current_section:
        current_section = milestone.section
        phase_session_id = None
    elif not phase_sessions_enabled:
        phase_session_id = None
    phase_session_id = process_milestone(project_dir, milestone, i, ...)
```

### Target change

Replace the fixed `for` with a re-scanning `while`. Extract a shared helper so both loops use identical selection logic and only differ in the per-milestone processing function.

```python
def _run_dynamic_loop(project_dir, roadmap_path, config, process_fn) -> None:
    """Re-parse the roadmap before each milestone, run the first pending one top-to-bottom."""
    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    phase_sessions_enabled = config.enable_phase_sessions

    # Startup summary (printed once)
    result = parse_roadmap(roadmap_path)
    pending = [m for m in result.milestones if not m.done]
    if not pending:
        print("All milestones are done!")
        return
    if result.breakpoint_hit:
        total = len(result.milestones) + result.milestones_after_breakpoint
        print(f"Found {len(pending)} pending milestones out of {total} total "
              f"(stopped at breakpoint — {result.milestones_after_breakpoint} after marker not queued).")
    else:
        print(f"Found {len(pending)} pending milestones out of {len(result.milestones)} total.")

    current_section: str | None = None
    phase_session_id: str | None = None
    last_signature: tuple[str, str] | None = None   # safety net, see below

    while not state.stop_requested:
        result = parse_roadmap(roadmap_path)                 # fresh scan every iteration
        pending = [m for m in result.milestones if not m.done]
        if not pending:
            break
        milestone = pending[0]                                # first unchecked, top-to-bottom

        signature = (milestone.title, milestone.description)
        if signature == last_signature:
            raise PipelineStopError(
                f"Milestone {milestone.title!r} was processed but its checkbox is still "
                f"unchecked — refusing to re-run it forever. Check ROADMAP.md and marking."
            )
        last_signature = signature

        i = _next_number(plans_dir)
        _check_usage_limits(config)
        if milestone.section != current_section:
            current_section = milestone.section
            phase_session_id = None
        elif not phase_sessions_enabled:
            phase_session_id = None
        print(f">>> picking: {milestone.title}")
        phase_session_id = process_fn(milestone, i, phase_session_id)

    if state.stop_requested:
        print("\n>>> Stop requested — halting.")
```

`_implement_loop` and `_test_loop` become thin wrappers binding `process_fn`:

```python
def _implement_loop(project_dir, config, planner_prompt_name="planner", roadmap_filename="ROADMAP.md"):
    roadmap_path = project_dir / ".ai-factory" / roadmap_filename
    if not roadmap_path.exists():
        print(f"ERROR: No {roadmap_filename} found at {roadmap_path}"); sys.exit(1)
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_milestone(
            project_dir, m, i, config, planner_prompt_name, roadmap_filename, phase_session_id=sid),
    )

def _test_loop(project_dir, config):
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP_TESTS.md"
    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP_TESTS.md found at {roadmap_path}"); sys.exit(1)
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_test_milestone(project_dir, m, i, config, phase_session_id=sid),
    )
```

### Why the safety net stays even with note 14

Note 14 makes mis-marks improbable, but the loop should never be able to spin forever on a single milestone if some other edge (a title the marker can't locate AND a stale `line_number` that points at an already-checked line) leaves the box unchecked. Tracking `last_signature` and raising `PipelineStopError` when the same `(title, description)` is selected twice in a row converts a hypothetical infinite loop into a clear stop. It does not interfere with normal progress — consecutive *different* milestones reset it, and re-selecting a genuinely new task with a coincidentally identical title only triggers after that task failed to flip, which is the exact condition we want to catch.

### Interaction with seq / resume

- `i = _next_number(plans_dir)` is computed fresh each iteration. After a milestone completes, its plan file exists, so the next `_next_number` naturally increments.
- Resume of an interrupted milestone still works: `_detect_milestone_step` / `_detect_test_milestone_step` resolve the canonical seq by globbing `*-{slug}.md`, so even though `_next_number` may return a higher number, the existing lower-seq plan file is found and reused.
- `---STOP---` handling is unchanged — `parse_roadmap` already excludes milestones after the marker, so they never enter `pending`.

### Scope

`orchestrator/main.py` only. `process_milestone` / `process_test_milestone` signatures unchanged. Remove the now-unused fixed-`pending` iteration from both loops. `_run_loop` (the generic stop-checking iterator) may remain for any other caller but is no longer used by these two loops.

### Verify

- Add a new pending task above an existing pending one mid-run (simulate by editing the file between iterations) → the newly-inserted task is selected next, before the lower one.
- Mark all tasks done → loop prints "All milestones are done!" and exits.
- A milestone that fails to flip its checkbox triggers the `last_signature` guard and stops with `PipelineStopError` rather than looping.
- `Ctrl+C` (`state.stop_requested`) breaks the loop and prints the halt message.

## Open Questions

None.
