# Project Roadmap

> Orchestrator — AI-driven multi-agent pipeline that autonomously plans, implements, and reviews code milestones.

## Milestones

- [x] **Orchestrator state file** — Add `orchestrator-state.json` to track inter-run state. Implement `_load_state` / `_save_state` helpers. Record review file names created during implement phase so they can be selectively deleted before the review phase, instead of wiping all reviews indiscriminately.

- [x] **Preparatory refactor** — Two small changes before refactor mode. (1) Replace hardcoded `MAX_REVIEW_ITERATIONS = 3` with env var `ORCHESTRATOR_MAX_REVIEW_ITERATIONS` (default 3); add `ORCHESTRATOR_MAX_REFACTOR_ITERATIONS` (default 2); pass limits as parameters to `process_milestone()` instead of reading the global. (2) Add `PipelineStopError(message)` to `agents.py`; catch it in `cli()` alongside `RateLimitError` — print message and exit 0.

- [x] **RefactorPlanner agent class** — Add `RefactorPlanner` to `agents.py` using `refactor-planner.md` as system prompt. Method `audit_and_plan(milestone_title, milestone_description, plan_path)` for the first iteration. Method `verify(plan_path, review_path)` for subsequent iterations — writes findings to review file, returns `True` if file ends with `REVIEW_PASS`, `False` otherwise. Same session across calls via `--resume`.

- [ ] **process_refactor_milestone function** — Add `process_refactor_milestone(project_dir, milestone, milestone_index)` to `main.py`. Chain: `RefactorPlanner.audit_and_plan` → `Implementer.implement` → `RefactorPlanner.verify`. On `REVIEW_PASS` mark done and git commit. If max iterations reached without `REVIEW_PASS` — raise `PipelineStopError` with the last review file path and its contents. Uses `ORCHESTRATOR_MAX_REFACTOR_ITERATIONS` limit.

- [ ] **refactor CLI command** — Add `refactor` subcommand to `cli()` in `main.py`. Reads ROADMAP.md, filters pending milestones, runs `process_refactor_milestone` for each. Wraps in `_with_caffeinate`. Handles `PipelineStopError` by printing findings and stopping — does not continue to next milestone.

## Completed

| Milestone | Date |
|-----------|------|
| Orchestrator state file | 2026-03-29 |
