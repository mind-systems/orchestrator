# Plan: RefactorPlanner agent class

## Context
Add a `RefactorPlanner` agent to `agents.py` that audits code areas and verifies fixes, using the existing `refactor-planner.md` system prompt and the same session-persistent pattern as `PlannerReviewer`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Agent class

- [x] **Task 1: Add RefactorPlanner class to agents.py**
  Files: `orchestrator/agents.py`
  Add the `RefactorPlanner` class after the existing `Implementer` class. Follow the same constructor pattern as `PlannerReviewer`:
  - `__init__(self, project_dir, model="opus", effort="high")` — load system prompt via `_load_prompt("refactor-planner")`, init `session_id = None`, set `tools = ["Read", "Write", "Glob", "Grep", "Bash"]` (same as `PlannerReviewer`).
  - `audit_and_plan(self, milestone_title, milestone_description, plan_path)` — build a prompt asking the agent to audit the code area described by the milestone and write a refactor plan to `plan_path`. Call `_run_claude()` with `system_prompt` (first call) and store `session_id`. Return `None`.
  - `verify(self, plan_path, review_path)` — build a prompt asking the agent to verify the implemented fixes against the plan at `plan_path` and write findings to `review_path`. Call `_run_claude()` with `session_id` for `--resume` (subsequent call pattern — pass `system_prompt` only when `session_id` is `None`, same guard as `PlannerReviewer.review`). After the call, read `review_path` and return `True` if it ends with `REVIEW_PASS`, `False` otherwise — same file-based check as `PlannerReviewer.review`.
