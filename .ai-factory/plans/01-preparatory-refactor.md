# Plan: Preparatory refactor

## Context
Replace the hardcoded `MAX_REVIEW_ITERATIONS` constant with env-var-driven configuration passed as function parameters, add a new `ORCHESTRATOR_MAX_REFACTOR_ITERATIONS` env var, and introduce a `PipelineStopError` exception for graceful pipeline halts.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: PipelineStopError exception

- [x] **Task 1: Add PipelineStopError to agents.py**
  Files: `orchestrator/agents.py`
  Add a `PipelineStopError(Exception)` class next to the existing `RateLimitError` (line 25). Single-arg `message` — no custom `__init__` needed, just inherit from `Exception`. Update the module so it's importable alongside `RateLimitError`.

### Phase 2: Replace hardcoded constant with env-var-driven parameters

- [x] **Task 2: Remove MAX_REVIEW_ITERATIONS global, read env vars in cli(), pass as parameters**
  Files: `orchestrator/main.py`
  1. Delete `MAX_REVIEW_ITERATIONS = 3` (line 34).
  2. In `cli()`, read two env vars into local variables:
     - `max_review = int(os.environ.get("ORCHESTRATOR_MAX_REVIEW_ITERATIONS", "3"))`
     - `max_refactor = int(os.environ.get("ORCHESTRATOR_MAX_REFACTOR_ITERATIONS", "2"))`
  3. Add `import os` at the top (already present in `agents.py` but not in `main.py`).
  4. Thread `max_review_iterations` parameter through every call path that currently reads the global:
     - `process_milestone(project_dir, milestone, milestone_index, max_review_iterations)` — replace both references to `MAX_REVIEW_ITERATIONS` inside the function with the parameter.
     - `review_plan(project_dir, plan_path, max_review_iterations)` — same treatment for its two references.
     - `_implement_loop(project_dir, max_review_iterations)` — accepts the parameter and forwards it to `process_milestone()`.
     - `run_implement(project_dir, max_review_iterations)` — accepts and forwards to `_implement_loop()`.
     - `run_implement_review(project_dir, max_review_iterations)` — accepts and forwards to both `_implement_loop()` and `run_review()`.
     - `run_review(project_dir, max_review_iterations)` — accepts and forwards to `review_plan()` inside the returned closure.
  5. In `cli()`, pass `max_review` to `run_implement()`, `run_implement_review()`, and `run_review()` at every call site. `max_refactor` is not used yet — it just needs to be read and available for future milestones.

- [x] **Task 3: Catch PipelineStopError in cli()**
  Files: `orchestrator/main.py`
  1. Add `PipelineStopError` to the import from `.agents` (line 14).
  2. In the `try/except` block in `cli()`, add an `except PipelineStopError as e:` handler alongside the existing `except RateLimitError`. Print the message and `sys.exit(0)` — same pattern as the `RateLimitError` handler.

### Phase 3: Wire max_refactor for future use

- [x] **Task 4: Store max_refactor_iterations as a passable parameter**
  Files: `orchestrator/main.py`
  In `cli()`, after reading `max_refactor` from the env var (Task 2 step 2), no further wiring is needed for now — the variable exists and will be passed to `process_refactor_milestone()` in a future milestone. Just ensure the env var read is present and the variable is available in scope for when the `refactor` subcommand is added.
