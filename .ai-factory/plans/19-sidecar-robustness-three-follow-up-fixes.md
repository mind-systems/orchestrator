# Plan: Sidecar robustness — three follow-up fixes

## Context

Harden the JSON sidecar layer introduced in milestone 18 against three concrete
crash-resilience and state-tracking bugs found during code review.

> **Scope correction:** The milestone description says "All three in `agents.py`
> only." That is accurate for Fix 1 and Fix 3. **Fix 2 lives in `orchestrator/main.py`**,
> not `agents.py`, because `process_milestone()` and `process_test_milestone()` are
> defined there (verified: `main.py:149` and `main.py:577`). The `_write_session`
> helper used by Fix 2 is imported from `agents.py` into `main.py`
> (`main.py:13`), so the fix uses the same API but is applied at the call site.

## Settings

- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Fix 1 — Fault-tolerant `_read_sessions`

- [x] **Task 1: Wrap `_read_sessions` JSON parse in try/except**
  Files: `orchestrator/agents.py`
  Modify `_read_sessions` (currently at `agents.py:24-28`). Wrap
  `json.loads(p.read_text())` in a `try/except (json.JSONDecodeError, OSError)`
  and return `{}` on failure. This restores the fault-tolerance the old regex
  parser had — a corrupt or truncated sidecar (e.g. from `kill -9` between
  truncate and write) should be treated as "no recorded sessions" rather than
  crashing the run. Target shape:
  ```python
  def _read_sessions(plan_path: Path) -> dict[str, str]:
      p = plan_path.with_suffix('.json')
      if not p.exists():
          return {}
      try:
          return json.loads(p.read_text())
      except (json.JSONDecodeError, OSError):
          return {}
  ```

### Phase 2: Fix 3 — Atomic sidecar write

- [x] **Task 2: Make `_write_session` atomic via tmp + `os.replace`**
  Files: `orchestrator/agents.py`
  Modify `_write_session` (currently at `agents.py:31-35`). Write the new JSON
  payload to a sibling tmp path (`p.with_suffix('.json.tmp')`) first, then
  atomically replace the target with `os.replace(tmp, p)`. This eliminates the
  truncate-then-write window that `Path.write_text` exposes. `os` is already
  imported at `agents.py:6`. Target shape:
  ```python
  def _write_session(plan_path: Path, key: str, value: str) -> None:
      p = plan_path.with_suffix('.json')
      data = json.loads(p.read_text()) if p.exists() else {}
      data[key] = value
      tmp = p.with_suffix('.json.tmp')
      tmp.write_text(json.dumps(data, indent=2))
      os.replace(tmp, p)
  ```
  Note: this Task 2 read of `p.read_text()` is still wrapped logically by
  Task 1's protections only inside `_read_sessions`; here the read path is the
  pre-existing behavior of `_write_session` (unchanged). Do **not** alter
  semantics beyond the atomic-replace pattern.

### Phase 3: Fix 2 — Persist `review_failed:N` / `test_run_failed:N` before raising

- [x] **Task 3: Reorder `_write_session` before `PipelineStopError` in `process_milestone()`**
  Files: `orchestrator/main.py`
  In `process_milestone()` (review loop, currently `main.py:270-277`), the
  current order is:
  ```python
  if iteration == max_iterations:
      raise PipelineStopError(...)
  _write_session(plan_path, "step", f"review_failed:{iteration}")
  ```
  Move the `_write_session(..., "step", f"review_failed:{iteration}")` call so
  that it runs **before** the `if iteration == max_iterations:` guard. This
  ensures that when the last attempt fails, the sidecar records
  `step="review_failed:N"` rather than retaining the prior `"implemented"`
  step. On the next run, `_detect_milestone_step` will then route to the
  fix-iteration branch instead of starting a fresh review and overwriting
  `review-1.md`.

- [x] **Task 4: Reorder `_write_session` before `PipelineStopError` in `process_test_milestone()`**
  Files: `orchestrator/main.py`
  Apply the symmetric fix in `process_test_milestone()` (test loop, currently
  `main.py:694-704`): move
  `_write_session(plan_path, "step", f"test_run_failed:{iteration}")` so it
  runs **before** the `if iteration == max_iterations:` guard that raises
  `PipelineStopError`. Same rationale — preserve failure step in the sidecar
  so a subsequent run resumes correctly instead of overwriting the prior
  `test-run-1.md` / `patch-1.md`.

  Important: the existing code at `main.py:697-698` also writes a bridge
  patch file (`patch_path.write_text(test_run_path.read_text())`) before the
  max-iterations check. Keep that bridge write where it is — it is
  independent of the sidecar step write. Only the `_write_session` step call
  moves.

## Verification (manual, no test task added)

After edits, confirm by inspection only (no test suite exists per
`CLAUDE.md`):
1. `_read_sessions` returns `{}` for a sidecar containing `""` or `"{bad"`.
2. `_write_session` no longer calls `Path.write_text` on the final sidecar
   path directly; only via the tmp path + `os.replace`.
3. Both `process_milestone()` and `process_test_milestone()` write the
   `*_failed:N` step before any `raise PipelineStopError(...)` in their
   respective review/test loops.

## Commit Plan

Four small, tightly-related tasks all in service of one milestone — single
commit at the end. No commit plan needed.
