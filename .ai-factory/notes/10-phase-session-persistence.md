# Phase-persistent PlannerReviewer session

**Date:** 2026-06-17
**Source:** conversation context

## Key Findings

- Any `##` or `###` heading in ROADMAP.md is a phase boundary — works across all project formats without modifying existing roadmaps
- Within a section, carry the planner's `session_id` from milestone N to milestone N+1 so it doesn't re-read DESCRIPTION.md, ARCHITECTURE.md, and spec notes from scratch
- PlannerReviewer uses Opus 4.8 with 1M context window — no hard cap needed; context bloat is not a concern
- Phase session is in-memory only — not persisted to disk; on process restart the optimizer is simply lost (no correctness issue)
- Milestone-level sidecar session takes priority over phase session on resume

## Details

### Milestone dataclass change (`roadmap.py`)

Add `section: str | None` to `Milestone`:

```python
@dataclass
class Milestone:
    title: str
    description: str
    done: bool
    line_number: int
    section: str | None = None  # nearest ## or ### heading above this milestone
```

In `parse_roadmap()`, track `current_section` while scanning lines:

```python
current_section: str | None = None
for line in lines:
    stripped = line.strip()
    if stripped.startswith("## ") or stripped.startswith("### "):
        current_section = stripped.lstrip("#").strip()
    elif stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
        # parse milestone as today, then:
        milestone.section = current_section
```

Lines starting with `---STOP---`, blank lines, and task description continuations do not reset the section.

### process_milestone signature change (`agents.py`)

```python
def process_milestone(
    project_dir, milestone, milestone_index, max_iterations=3,
    planner_prompt_name="planner", roadmap_filename="ROADMAP.md",
    phase_session_id: str | None = None,
) -> str | None:  # returns planner session_id for phase continuity
```

Session priority when initializing `PlannerReviewer`:
1. Sidecar has `planner` key → use it (milestone resume takes priority)
2. Sidecar has no `planner` AND `phase_session_id` is provided → use `phase_session_id`
3. Neither → `None` (start fresh)

```python
sessions = _read_sessions(plan_path)
if sessions.get("planner"):
    planner_reviewer.session_id = sessions["planner"]
elif phase_session_id:
    planner_reviewer.session_id = phase_session_id
```

Return at the end of the function:
```python
return planner_reviewer.session_id
```

Same change for `process_test_milestone`.

### Loop change (`main.py`)

Replace `_run_loop(...)` call in `_implement_loop` and `_test_loop` with an inline loop that threads phase session state:

```python
current_section: str | None = None
phase_session_id: str | None = None

for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
    if _state.stop_requested:
        print(">>> Stop requested — halting.")
        break
    if milestone.section != current_section:
        current_section = milestone.section
        phase_session_id = None  # reset at every ## or ### boundary
    phase_session_id = process_milestone(
        project_dir, milestone, i, max_iterations,
        planner_prompt_name, roadmap_filename,
        phase_session_id=phase_session_id,
    )
```

`_run_loop` function can be kept or removed — it's no longer called from the main loops. If kept, it remains for potential future use.

### Why no disk persistence of phase session

The phase session is an optimization: it saves the planner from re-reading DESCRIPTION.md, ARCHITECTURE.md, and spec notes at the start of each milestone. If the process restarts between milestones, the planner loses this warmth — but starts fresh for the next milestone (correct, just slightly slower). Persisting the phase session to disk adds complexity with marginal benefit.

### Files to touch

- `orchestrator/roadmap.py`: `Milestone.section` field + `parse_roadmap()` section tracking
- `orchestrator/agents.py`: `process_milestone()` and `process_test_milestone()` — accept `phase_session_id`, session priority logic, return session_id
- `orchestrator/main.py`: `_implement_loop()` and `_test_loop()` — inline the loop with section tracking; `_run_loop` can be left or removed
