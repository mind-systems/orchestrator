# Rename `milestone` code identifiers to `task`

**Date:** 2026-07-13
**Source:** conversation context

## Problem today

The orchestrator's processed roadmap unit is the reserved word **`task`**, but the Python surface still names it `milestone` throughout — the `Milestone` dataclass, the functions that operate on it, and the locals/params/state that carry it. The code does not yet speak the language it stores. This task renames every such identifier to `task`, behavior-neutrally, so the code (and its tests) read in the canonical vocabulary the later phases reference.

Verified resume-safety: the on-disk sidecar keys (`planner`, `implementer`, `step`, `elapsed`) and every `step` value carry no "milestone"; `state.milestones_done` is an in-memory counter; artifact filenames key on `.slug`, not on the symbol name. So no rename here touches an on-disk format — resume stays byte-stable.

## The change

Rename these identifiers across `orchestrator/*.py` **and** `tests/*.py`, at every reference, so the suite stays green:

| Current | New |
|---|---|
| `Milestone` (dataclass, `roadmap.py`) | `Task` |
| `_MilestoneStub` (test helper) | `_TaskStub` |
| `process_milestone` (`main.py`) | `process_task` |
| `_find_milestone_line` (`roadmap.py`) | `_find_task_line` |
| `_detect_milestone_step` (`resume.py`) | `_detect_task_step` |
| `_detect_test_milestone_step` (`resume.py`) | `_detect_test_task_step` |
| `milestone_index` / `milestone_start` / `milestone_title` / `milestone_description` | `task_index` / `task_start` / `task_title` / `task_description` |
| `milestones_done` (`state.py`) | `tasks_done` |
| `milestones_after_breakpoint` (`roadmap.py`, `main.py`) | `tasks_after_breakpoint` |
| locals `milestone` / `milestones` | `task` / `tasks` |
| test names `test_detect_milestone_step_*`, `test_detect_test_milestone_step_*`, `test_find_milestone_line_*`, `test_process_milestone_*`, `test_parse_roadmap_milestones_after_breakpoint_count` | the same with `milestone`→`task` |

**In scope too:** the in-code prose — docstrings and comments that say "milestone" (e.g. `roadmap.py:87` `"""Mark a milestone as completed…"""`, `main.py:1` `"""…loop through roadmap milestones."""`, the `PlannerReviewer` docstring `"""Plans and reviews milestones…"""`). Rename these to `task` alongside the identifiers — they live in the same files and a renamed symbol with a stale docstring is an incoherent half-state.

## The one hard constraint — this is not a blind replace

Some lines carry an identifier **and** a user-facing string literal at once. Rename the identifier; leave the string literal's contents byte-for-byte. Example:

```python
notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")
```

→ `milestone.title` becomes `task.title`; the text `"Milestone done"` and the token `"milestone"` **stay unchanged** (they belong to Phase 6). Same shape in `runtime.py:39` (`state.milestones_done` → `state.tasks_done`, but the summary word "milestones done" stays). A global `s/milestone/task/g` would wrongly rewrite these strings and pre-empt Phase 6's breaking-change decision — do the rename symbol-aware.

## Verify

- `uv run pytest` green — the whole suite renamed with the source, nothing weakened.
- `grep -rnE '[A-Za-z_]*[Mm]ilestone[A-Za-z_]*' orchestrator/*.py tests/*.py` returns **only**: (a) occurrences inside user-facing string literals (the `"Milestone done"` / `"milestone"` / `"milestone-fail"` / `print("…milestones…")` set that Phase 6 owns), and (b) the three alert-token test names — `test_milestone_fail_alert_prefixed_red`, `test_milestone_alert_prefixed_green` (`test_notify.py`), `test_cli_pipeline_stop_error_routes_to_milestone_fail` (`test_main.py`) — with their docstrings and assertions, which name the alert-token literal under test and so rename together with it in task 6.1, not here. No other identifier, docstring, or comment survives.
- No on-disk artifact format changed: a resume across this rename behaves identically.

## What NOT to do

- Do **not** touch user-facing string literals, Telegram alert tokens (`"milestone"`, `"milestone-fail"`, `_FAIL_ALERTS`), console `print` wording, or config — that is Phase 6, a deliberately separate breaking change.
- Do **not** rename the `Milestone.slug` attribute's *concept* or otherwise touch `slug` — its collision with the reserved word `slug` is a separate concern, out of scope here.
- Do **not** change any behavior — this is a pure rename; the only diff is names and in-code prose.

## Tests

No new tests. The existing suite already covers these surfaces; it is renamed in lockstep with the source and must stay green (a rename that breaks a test means a missed reference, not a needed new test).
