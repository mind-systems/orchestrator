# Code Review: Lazy `_CLAUDE_BIN` resolution

## Scope
Reviewed `git diff HEAD` and `git status`. The only source change is in `orchestrator/agents.py`. The staged new files under `.ai-factory/` are plan/review artifacts, not code.

## Changes
- `_CLAUDE_BIN = _resolve_claude()` (import-time) → `_CLAUDE_BIN: str | None = None`.
- `_run_claude()` resolves lazily on first call and caches:
  ```python
  global _CLAUDE_BIN
  if _CLAUDE_BIN is None:
      _CLAUDE_BIN = _resolve_claude()
  ```

## Verification
- **Correctness:** The lazy-cache pattern is valid Python. `_CLAUDE_BIN` is resolved before the `cmd` list is built (line 115), so it is never `None` at the point of use.
- **Runtime contract preserved:** `_resolve_claude()` is unchanged and still raises `FileNotFoundError` when the CLI is missing — the failure is merely deferred from import time to first call, which is the intended behavior.
- **Blast radius:** Grep confirms `_CLAUDE_BIN` is referenced only within `agents.py` (definition, lazy guard, `cmd` use). No other module imports the symbol, so there is no external impact.
- **Goal met:** The module no longer has an import-time side effect, so `agents.py` can be imported without the `claude` CLI installed — the stated prerequisite for unit tests.
- **Concurrency:** Single-process CLI tool; the non-atomic check-then-set is benign and consistent with the existing code's threading model. Worst case is a redundant `_resolve_claude()` call, which is idempotent.
- **Type annotation:** `str | None` matches the codebase's existing style.

## Findings
None.

REVIEW_PASS
