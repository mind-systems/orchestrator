# Plan: Resume guard + write hardening

## Context
Three follow-up fixes from milestone 19's code review: prevent silent commit of unfinished code when resuming past `max_iterations`, harden `_write_session` against a corrupt sidecar, and stop stale `*.json.tmp` files from being committed. Spec: `.ai-factory/notes/06-resume-guard-and-write-hardening.md`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Resume guard

- [x] **Task 1: Guard `process_milestone` implement/review loop against empty resume range**
  Files: `orchestrator/main.py`
  In `process_milestone()`, immediately after `impl_start = counter if step in ("implement", "review") else 1` (around line 250) and before the `for iteration in range(impl_start, max_iterations + 1):` loop, add:
  ```python
  if impl_start > max_iterations:
      raise PipelineStopError(
          f"Resume at iteration {impl_start} exceeds max_iterations "
          f"({max_iterations}). Bump ORCHESTRATOR_MAX_ITERATIONS to continue."
      )
  ```
  `PipelineStopError` is already imported from `.agents` at the top of the file — no new import needed. This prevents the silent `mark_done()` + `_git_commit()` fall-through described in the spec, where a sidecar `step="review_failed:3"` with default `max_iterations=3` produces `range(4, 4)` (empty loop) and commits unfinished code.

- [x] **Task 2: Guard `process_test_milestone` implement/test_run loop with the same check** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `process_test_milestone()`, immediately after `impl_start = counter if step in ("implement", "test_run") else 1` (around line 675) and before the `for iteration in range(impl_start, max_iterations + 1):` loop, add the identical `PipelineStopError` guard from Task 1. Same rationale: `step="test_run_failed:N"` at `max_iterations` would otherwise resume into an empty range and commit unfinished test code.

### Phase 2: Write hardening

- [x] **Task 3: Guard `_write_session` internal read against corrupt sidecar**
  Files: `orchestrator/agents.py`
  In `_write_session()` (lines 34-40 of `orchestrator/agents.py`), replace the unguarded `data = json.loads(p.read_text()) if p.exists() else {}` with a try/except matching the pattern already used by `_read_sessions` (lines 28-31):
  ```python
  def _write_session(plan_path: Path, key: str, value: str) -> None:
      p = plan_path.with_suffix('.json')
      try:
          data = json.loads(p.read_text()) if p.exists() else {}
      except (json.JSONDecodeError, OSError):
          data = {}
      data[key] = value
      tmp = p.with_suffix('.json.tmp')
      tmp.write_text(json.dumps(data, indent=2))
      os.replace(tmp, p)
  ```
  This completes milestone 19 Fix 1's resilience guarantee: a sidecar left corrupt by a pre-milestone-19 crash currently survives `_read_sessions` (returns `{}`) but crashes the next `_write_session` call with `JSONDecodeError`. After this change, a corrupt sidecar is silently rewritten with fresh content. `json` and `os` are already imported at the top of the file.

### Phase 3: Gitignore

- [x] **Task 4: Add `*.json.tmp` to `.gitignore`**
  Files: `.gitignore`
  Append a new section at the end of `/Users/max/projects/orchestrator/.gitignore`:
  ```
  # Sidecar atomic-write temp files
  *.json.tmp
  ```
  Prevents stale `*.json.tmp` files (left behind when `kill -9` interrupts `_write_session` between `tmp.write_text(...)` and `os.replace(tmp, p)`) from being staged by `git add -A` in the next `_git_commit()` and committed as orphaned artifacts.
