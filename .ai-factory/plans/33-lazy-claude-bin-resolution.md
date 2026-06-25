# Plan: Lazy `_CLAUDE_BIN` resolution

## Context
Make `agents.py` importable without the `claude` CLI installed by resolving the binary path lazily on first call instead of at module import time. This unblocks any unit test that imports `agents.py`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Lazy resolution

- [x] **Task 1: Replace eager resolution with a lazy cache**
  Files: `orchestrator/agents.py`
  Change the module-level `_CLAUDE_BIN = _resolve_claude()` (line ~94) to a lazily-initialized cache: `_CLAUDE_BIN: str | None = None`. Keep `_resolve_claude()` unchanged (it stays the resolver, still raising if `claude` is not found). This removes the import-time side effect so the module can be imported without the CLI present.

- [x] **Task 2: Resolve on first use inside `_run_claude()`** (depends on Task 1)
  Files: `orchestrator/agents.py`
  At the start of `_run_claude()` (before the `cmd` list is built, around line 110), add lazy resolution and caching:
  ```python
  global _CLAUDE_BIN
  if _CLAUDE_BIN is None:
      _CLAUDE_BIN = _resolve_claude()
  ```
  Leave the existing `_CLAUDE_BIN` reference in the `cmd` list (line ~111) as-is; it now reads the cached value. Resolution failure (CLI missing) still raises at call time, not at import time — preserving current runtime behavior.
