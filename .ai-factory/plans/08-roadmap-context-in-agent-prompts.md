# Plan: Roadmap context in agent prompts

## Context
Add roadmap file path and line number to agent prompts so agents can optionally read the full roadmap for context about what's already done and what comes next.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Agent method signatures and prompts

- [x] **Task 1: Add roadmap context to PlannerReviewer.plan()**
  Files: `orchestrator/agents.py`
  Add optional parameters `roadmap_path: Path | None = None` and `line_number: int | None = None` to `plan()`. In the first-call branch (when `plan_review_path` is None), prepend `"Roadmap: {roadmap_path} (line {line_number + 1})\n"` before the `**{milestone_title}**` line — only when both params are provided. The revision branch (when `plan_review_path` is set) stays unchanged — the agent already has context from the first call via `--resume`.

- [x] **Task 2: Add roadmap context to RefactorPlanner.audit_and_plan()**
  Files: `orchestrator/agents.py`
  Add the same optional parameters `roadmap_path: Path | None = None` and `line_number: int | None = None` to `audit_and_plan()`. Prepend the same `"Roadmap: {roadmap_path} (line {line_number + 1})\n"` line before `**{milestone_title}**` in the prompt — only when both params are provided.

- [x] **Task 3: Add roadmap context to Implementer.implement()**
  Files: `orchestrator/agents.py`
  Add optional parameters `roadmap_path: Path | None = None` and `line_number: int | None = None` to `implement()`. In the first-call branch (when `self.session_id` is falsy), prepend `"Roadmap: {roadmap_path} (line {line_number + 1})\n"` before the existing `"Implement the plan at: {plan_path}"` line — only when both params are provided. The continuation branch (when `self.session_id` is set) stays unchanged.

### Phase 2: Pass values from call sites

- [x] **Task 4: Wire roadmap context in process_milestone()** (depends on Tasks 1, 3)
  Files: `orchestrator/main.py`
  Move `roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"` to the top of the function (before the agents are created), replacing the later assignment at line 160. Pass `roadmap_path=roadmap_path, line_number=milestone.line_number` to `planner_reviewer.plan()` (line 104) and `implementer.implement()` (line 141). The `plan()` revision call (line 130-133) does not need these params — it already has session context.

- [x] **Task 5: Wire roadmap context in process_refactor_milestone()** (depends on Tasks 2, 3)
  Files: `orchestrator/main.py`
  Same pattern: move `roadmap_path` assignment to the top of the function, replacing the later one at line 219. Pass `roadmap_path=roadmap_path, line_number=milestone.line_number` to `refactor_planner.audit_and_plan()` (line 192) and `implementer.implement()` (line 197).
