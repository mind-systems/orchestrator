# Plan: Caffeinate no-crash on non-macOS

## Context
Make `_with_caffeinate` in `main.py` degrade gracefully on platforms without the `caffeinate` binary (e.g. Linux), instead of crashing with `FileNotFoundError`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Harden caffeinate spawn

- [x] **Task 1: Guard `caffeinate` spawn against missing binary**
  Files: `orchestrator/main.py`
  In `_with_caffeinate` (currently ~line 396-416), wrap the `subprocess.Popen(["caffeinate", "-ims"])` call in `try/except FileNotFoundError`.
  - On macOS (Popen succeeds): keep existing behavior exactly — start timer, run `func(*args, **kwargs)`, handle the `except Exception` elapsed-print/re-raise path, and in `finally` send `SIGTERM` to the caffeinate process and `wait()` for it. Return the formatted elapsed string.
  - On non-macOS (`FileNotFoundError`): run the wrapped function directly without spawning/managing any caffeinate process, then return the same `"{hours}h {mins}m {secs}s"` / `"{mins}m {secs}s"` formatted elapsed string. Preserve the same error path (print `>>> Ran for ...` elapsed line before re-raising on exception) so behavior matches the caffeinated branch aside from sleep prevention.
  Keep the elapsed-formatting logic identical between both branches (factor it so there is no duplication divergence, e.g. a small inner helper or shared formatting). No behavior change on macOS.
