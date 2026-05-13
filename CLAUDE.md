# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
cd orchestrator && uv sync

# Plan + implement milestones (no review pass)
uv run orchestrator implement /path/to/project

# Review all existing plans against current codebase
uv run orchestrator review /path/to/project

# Implement milestones, then run review pass on all plans
uv run orchestrator implement-review /path/to/project

# Audit + refactor pending milestones (RefactorPlanner finds issues itself)
uv run orchestrator refactor /path/to/project

# Write tests for milestones from ROADMAP_TESTS.md
uv run orchestrator test /path/to/project

# Default (implement) on current directory
uv run orchestrator
```

No test suite or linter is configured.

## Architecture

Four-agent pipeline that processes milestones from a target project's `.ai-factory/ROADMAP.md`:

1. **PlannerReviewer** (`agents.py`) — Opus/high. Session-persistent. Writes the plan, then later reviews code changes in the same session (so the reviewer has full planner context).
2. **PlanReviewer** (`agents.py`) — Opus/high. Fresh session per attempt. Reviews the plan *before* implementation starts, writes `PLAN_REVIEW_PASS` or findings to `.ai-factory/plan-reviews/`.
3. **Implementer** (`agents.py`) — Sonnet/high. Session-persistent across implement → fix iterations.
4. **RefactorPlanner** (`agents.py`) — Opus/high. Session-persistent. Used only in `refactor` mode: audits a code area, writes a plan, then verifies fixes in the same session.
5. **TestRunner** (`agents.py`) — No LLM. Used only in `test` mode: reads `## Test Command` from the plan file, runs it via shell, writes stdout+exit code to `.ai-factory/test-runs/`. Returns `True` if exit code is 0.

Pipeline per milestone (`implement` mode):

```
PlannerReviewer.plan()
  └─► PlanReviewer.review_plan()  ×N  (FAIL → PlannerReviewer.plan() again)
        └─► Implementer.implement()
              └─► PlannerReviewer.review()  ×N  (FAIL → Implementer.implement() again)
                    └─► mark_done() + git commit
```

Pipeline per milestone (`test` mode):

```
PlannerReviewer.plan()      ← uses test-planner prompt
  └─► PlanReviewer.review_plan()  ×N  (FAIL → PlannerReviewer.plan() again)
        └─► Implementer.implement()
              └─► TestRunner.run()  ×N  (FAIL → Implementer.implement() again)
                    └─► mark_done() + git commit
```

All agents communicate through files, not shared memory. Output directories under `.ai-factory/`: `plans/`, `plan-reviews/`, `reviews/`, `patches/`, `test-runs/`.

`_run_claude()` in `agents.py` shells out to the `claude` CLI with `--output-format json` and parses `result`/`session_id`. Pass/fail is detected by `PLAN_REVIEW_PASS` (plan review) or `REVIEW_PASS` (code review) as the last line of the respective file.

## Target project requirements

The project being orchestrated must have:
- `.ai-factory/ROADMAP.md` with milestones formatted as:
  ```
  - [ ] **Title** — Description
  ```
- `.ai-factory/DESCRIPTION.md` — tech stack and conventions (read by the planner agent)
- An initialized git repo (the orchestrator commits after each milestone)

For `test` mode, milestones are read from `.ai-factory/ROADMAP_TESTS.md` (same format). This file is separate from `ROADMAP.md` so test tasks don't pollute the main roadmap.

## Key constants

- `ORCHESTRATOR_MAX_ITERATIONS` env var (default 3) — single iteration limit for all flows (plan review, implement review, refactor verify)
- Default models/effort: PlannerReviewer=opus/high, PlanReviewer=opus/high, Implementer=sonnet/high, RefactorPlanner=opus/high — override when instantiating agents in `process_milestone()` / `process_refactor_milestone()`
