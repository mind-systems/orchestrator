# Plan: Unified iteration limit

## Context
Replace the two separate env vars and parameter names for iteration limits (`ORCHESTRATOR_MAX_REVIEW_ITERATIONS` / `ORCHESTRATOR_MAX_REFACTOR_ITERATIONS`) with a single `ORCHESTRATOR_MAX_ITERATIONS` env var (default 3) and a unified `max_iterations` parameter threaded through every function.

Note: This unification changes the refactor flow default from 2 → 3 iterations, since both flows will now share the single default of 3. This is intentional — the roadmap requires all flows to use one value.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Unify env var and rename parameters

- [x] **Task 1: Replace env vars in `cli()` with single `ORCHESTRATOR_MAX_ITERATIONS`**
  Files: `orchestrator/main.py`
  In `cli()` (around lines 451-452), delete the two env var reads:
  ```python
  max_review = int(os.environ.get("ORCHESTRATOR_MAX_REVIEW_ITERATIONS", "3"))
  max_refactor = int(os.environ.get("ORCHESTRATOR_MAX_REFACTOR_ITERATIONS", "2"))
  ```
  Replace with one:
  ```python
  max_iterations = int(os.environ.get("ORCHESTRATOR_MAX_ITERATIONS", "3"))
  ```
  Then update every call site inside `cli()` to pass `max_iterations` instead of `max_review` / `max_refactor`:
  - `run_review(project_dir, max_iterations)`
  - `run_implement_review(project_dir, max_iterations)`
  - `run_refactor(project_dir, max_iterations)`
  - `run_implement(project_dir, max_iterations)`

- [x] **Task 2: Rename parameter in all top-level `run_*` functions**
  Files: `orchestrator/main.py`
  Rename the parameter from `max_review_iterations` / `max_refactor_iterations` to `max_iterations` (default 3) in every top-level runner:
  - `run_implement(project_dir, max_iterations: int = 3)` — pass through to `_implement_loop`
  - `run_refactor(project_dir, max_iterations: int = 3)` — pass through to `_refactor_loop`
  - `run_implement_review(project_dir, max_iterations: int = 3)` — pass through to `_implement_loop` and `run_review`
  - `run_review(project_dir, max_iterations: int = 3)` — pass through to `review_plan`
  Update every internal reference in each function body to use the new name.

- [x] **Task 3: Rename parameter in internal loop functions**
  Files: `orchestrator/main.py`
  Rename and unify the parameter in:
  - `_implement_loop(project_dir, max_iterations: int = 3)` — passes it to `process_milestone`
  - `_refactor_loop(project_dir, max_iterations: int = 3)` — passes it to `process_refactor_milestone`
  Update every internal reference in each function body to use the new name.

- [x] **Task 4: Rename parameter in `process_milestone`, `process_refactor_milestone`, and `review_plan`**
  Files: `orchestrator/main.py`
  Rename and unify:
  - `process_milestone(... max_iterations: int = 3)` — update the `range()` call and the max-reached warning to use `max_iterations`
  - `process_refactor_milestone(... max_iterations: int = 3)` — update the `range()` call and the `PipelineStopError` message to use `max_iterations`
  - `review_plan(... max_iterations: int = 3)` — update the `range()` call and the max-reached warning to use `max_iterations`
  Every log/error message that currently references "review iterations" or "refactor iterations" should just say "iterations".

- [x] **Task 5: Update `CLAUDE.md` and `DESCRIPTION.md` to reflect the new constant**
  Files: `CLAUDE.md`, `.ai-factory/DESCRIPTION.md`
  In `CLAUDE.md`:
  - Line 29: change `up to \`MAX_REVIEW_ITERATIONS\`` to `up to \`ORCHESTRATOR_MAX_ITERATIONS\`` (env var, default 3)
  - Line 47: replace `\`MAX_REVIEW_ITERATIONS = 3\` in \`main.py\`` with `\`ORCHESTRATOR_MAX_ITERATIONS\` env var (default 3) — single iteration limit for all flows`
  In `DESCRIPTION.md`:
  Replace the `MAX_REVIEW_ITERATIONS = 3` reference in the Key Constants section with `ORCHESTRATOR_MAX_ITERATIONS` env var (default 3). Remove any mention of separate review/refactor iteration limits.

## Commit Plan
- **Commit 1** (after tasks 1-5): "Unify iteration limit into single ORCHESTRATOR_MAX_ITERATIONS env var"
