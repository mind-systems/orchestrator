# Plan: Adaptive session usage guard

## Context
Add a usage guard that polls `claude /usage`, predicts the next check point adaptively from a rolling delta, and stops the pipeline before a milestone would breach the Claude Code 5-hour session limit.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Notes for implementer
- Touch **only** `orchestrator/main.py`.
- Full reference implementation lives in `.ai-factory/notes/09-adaptive-usage-guard.md` — follow its code closely.
- `PipelineStopError` is already imported in `main.py` (line 13); `re` and `math` are **not** imported yet.
- Important reconciliation: `_implement_loop` (line ~627) and `_test_loop` (line ~590) iterate with their own inline `for i, milestone in enumerate(pending, start=...)` loops — they do **not** call `_run_loop`. The milestone asks for two distinct things: (a) extend `_run_loop`'s signature with the optional `before_each` hook for backward compatibility, and (b) wire the guard into the two real loops directly via inline `guard.check(i)` calls. Do both.

## Tasks

### Phase 1: Usage parsing + guard primitive

- [x] **Task 1: Add imports**
  Files: `orchestrator/main.py`
  Add `import math` and `import re` to the top-level imports (alongside the existing `import os`, `import subprocess`, etc.). Keep alphabetical/stdlib grouping consistent with the current import block.

- [x] **Task 2: Add `_parse_usage_pct()` helper**
  Files: `orchestrator/main.py`
  Add module-level function `_parse_usage_pct() -> float | None` that runs `subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)`, searches stdout with regex `r"Current session:\s+(\d+(?:\.\d+)?)%\s+used"`, and returns `float(match.group(1))` or `None` when no match. Wrap the subprocess call defensively: on any exception (e.g. `subprocess.TimeoutExpired`, `FileNotFoundError`) return `None` rather than raising — the guard must degrade gracefully, never crash the pipeline. Place it near the other module-level helpers (e.g. after `_handle_sigint` / before or after `_run_loop`).

- [x] **Task 3: Add `UsageGuard` class** (depends on Task 2)
  Files: `orchestrator/main.py`
  Add a `UsageGuard` class as specified in the note:
  - `__init__(self, threshold: float = 90.0)` initializing `self.threshold`, `self._history: list[tuple[int, float]] = []`, and `self._next_check_at: int = 0`.
  - `check(self, idx: int) -> None`: return early if `idx < self._next_check_at`; otherwise call `_parse_usage_pct()`. If `None`, print `"  [usage check: could not parse output, continuing]"`, set `self._next_check_at = idx + 5`, and return. Print `f"  [usage: session {pct:.0f}% used]"`. If `pct >= self.threshold`, raise `PipelineStopError(f"Session usage at {pct:.0f}% — stopping (threshold: {self.threshold:.0f}%).")`. Otherwise append `(idx, pct)` to history and set `self._next_check_at = self._predict_next(idx, pct)`.
  - `_predict_next(self, idx: int, pct: float) -> int`: if fewer than 2 history points, return `idx + 1`. Else compute `span = idx - history[0][0]`; if `span == 0` return `idx + 5`; `avg_delta = (pct - history[0][1]) / span`; if `avg_delta <= 0` return `idx + 5`; else `milestones_left = math.ceil((self.threshold - pct) / avg_delta)` and return `idx + max(1, milestones_left - 1)`.

### Phase 2: Hook + wiring

- [x] **Task 4: Add optional `before_each` hook to `_run_loop`** (depends on Task 3)
  Files: `orchestrator/main.py`
  Extend `_run_loop(items, process_fn)` → `_run_loop(items, process_fn, before_each=None)`. Inside the loop, after the `state.stop_requested` check and before `process_fn(item)`, call `before_each(i, item)` when `before_each` is not None. The current loop iterates `for item in items` with no index — change it to `for i, item in enumerate(items)` so the index is available for the hook. Default `None` keeps existing callers backward-compatible.

- [x] **Task 5: Wire `UsageGuard` into `_implement_loop` and `_test_loop`** (depends on Task 3)
  Files: `orchestrator/main.py`
  In both `_implement_loop` and `_test_loop`, before entering the milestone `for` loop, read the threshold and create the guard:
  ```python
  threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))
  guard = UsageGuard(threshold=threshold)
  ```
  Inside each inline loop, after the `state.stop_requested` check and before the section/`process_*` call, invoke `guard.check(i)` (where `i` is the existing enumerate index). The raised `PipelineStopError` propagates up through `_with_caffeinate` to `cli()`, which already handles it — no extra try/except needed. Guard `float(...)` against a malformed env value is out of scope; default `"90"` is the documented behavior.

## Commit Plan
- **Commit 1** (after tasks 1-5): "Add adaptive session usage guard"
