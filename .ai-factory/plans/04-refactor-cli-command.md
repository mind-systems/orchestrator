# Plan: refactor CLI command

## Context
Add a `refactor` subcommand to the CLI that runs `process_refactor_milestone` for each pending milestone, following the same structural pattern as the existing `implement` command but stopping on `PipelineStopError` instead of continuing.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Refactor loop and CLI wiring

- [x] **Task 1: Add `_refactor_loop` function**
  Files: `orchestrator/main.py`
  Add `_refactor_loop(project_dir, max_refactor_iterations)` following the exact pattern of `_implement_loop` (lines 290-314). It should: read the roadmap, filter pending milestones, print count, iterate with `_next_number(plans_dir)` as start index, check `state.stop_requested` before each milestone, and call `process_refactor_milestone` instead of `process_milestone`. Pass `max_refactor_iterations` (not `max_review_iterations`) to `process_refactor_milestone`.

- [x] **Task 2: Add `run_refactor` function**
  Files: `orchestrator/main.py`
  Add `run_refactor(project_dir, max_refactor_iterations)` following the pattern of `run_implement` (lines 317-323). It should: set the SIGINT handler, call `_with_caffeinate(_refactor_loop, ...)`, and print the elapsed-time banner. Use `"REFACTOR DONE"` in the banner text.

- [x] **Task 3: Register `refactor` subcommand in `cli()`**
  Files: `orchestrator/main.py`
  Add `"refactor"` to the subcommand list (line 400-404) with help text `"Run refactor pipeline on pending milestones"`. Add a branch in the `try` block (around line 414) that calls `run_refactor(project_dir, max_refactor)` when `args.command == "refactor"`. The existing `PipelineStopError` handler already prints and exits — it covers this subcommand too. Note: the `PipelineStopError` from `process_refactor_milestone` will propagate up through `_refactor_loop` → `_with_caffeinate` → `run_refactor` and be caught by the existing handler in `cli()`, which stops execution — this naturally prevents continuing to the next milestone.
