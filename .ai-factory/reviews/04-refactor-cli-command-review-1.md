# Review: refactor CLI command

## Scope
Three additions to `orchestrator/main.py`: `_refactor_loop`, `run_refactor`, and the `refactor` subcommand in `cli()`.

## Analysis

### `_refactor_loop` (lines 317–341)
Exact structural mirror of `_implement_loop` (lines 290–314). Correctly:
- Reads roadmap, filters pending milestones
- Creates `plans_dir` and uses `_next_number` for sequential numbering
- Checks `state.stop_requested` before each milestone
- Calls `process_refactor_milestone` with `max_refactor_iterations` (not `max_review_iterations`)

### `run_refactor` (lines 353–359)
Mirrors `run_implement`. Correctly:
- Sets SIGINT handler
- Wraps loop in `_with_caffeinate`
- Prints "REFACTOR DONE" banner with elapsed time on success

### CLI wiring (lines 440, 462–463)
- Subcommand registered with correct help text
- Dispatches to `run_refactor(project_dir, max_refactor)`
- `max_refactor` reads from `ORCHESTRATOR_MAX_REFACTOR_ITERATIONS` env var (line 449, default 2) — already present from the preparatory refactor milestone

### Error propagation — "does not continue to next milestone"
Traced the full path: `process_refactor_milestone` raises `PipelineStopError` → breaks out of `_refactor_loop`'s for-loop → `_with_caffeinate` catches, prints elapsed time, re-raises → `run_refactor` does not catch → `cli()` catches at line 466, prints findings, exits 0. This correctly prevents any further milestones from running.

### Imports
`RefactorPlanner`, `PipelineStopError`, and all other dependencies already imported at line 14.

## Verdict
Clean implementation. No bugs, no missing edge cases, no security issues. Follows existing patterns exactly.

REVIEW_PASS
