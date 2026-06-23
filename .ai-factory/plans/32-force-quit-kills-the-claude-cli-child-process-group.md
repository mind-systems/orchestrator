# Plan: Force-quit kills the Claude CLI child process group

## Context
A double Ctrl+C ("Force quit") currently leaves the running `claude -p` child alive (it is a process-group leader via `start_new_session=True`, and the force-quit path raises `SystemExit` which bypasses the `except KeyboardInterrupt` cleanup). This milestone registers the in-flight child so the SIGINT handler can `SIGKILL` its whole process group before exiting.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: State registry

- [x] **Task 1: Add `active_proc` registry to state**
  Files: `orchestrator/state.py`
  Add `from __future__ import annotations` and `import subprocess` at the top. Add a module-level `active_proc: subprocess.Popen | None = None` alongside the existing `stop_requested: bool = False`. This is the single in-flight child slot — `_run_claude` runs one child at a time on the main thread, so one slot is sufficient. Keep `stop_requested` unchanged.

### Phase 2: Agent-side registration and group kill

- [x] **Task 2: Add `kill_active_child()` helper and `signal` import** (depends on Task 1)
  Files: `orchestrator/agents.py`
  Add `import signal` to the existing imports (`os` is already imported). Add a module-level `kill_active_child()` function: read `proc = state.active_proc`; if `proc is None` or already exited (`proc.poll() is not None`) just set `state.active_proc = None` and return. Otherwise call `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` to kill the whole process group (this also reaps any grandchildren the CLI spawned), wrapped in `try/except (ProcessLookupError, PermissionError)` that falls back to `proc.kill()`. Finally set `state.active_proc = None`. The guard against `ProcessLookupError` covers the race where the child already exited (e.g. force-quit landing during the retry `time.sleep`).

- [x] **Task 3: Register and clear `active_proc` in `_run_claude`** (depends on Task 2)
  Files: `orchestrator/agents.py`
  In `_run_claude`, immediately after `proc = subprocess.Popen(...)` (the call uses `start_new_session=True` — keep it; it is what makes the group addressable via the leader PID), set `state.active_proc = proc`. After the normal blocking read completes and `proc.wait()` returns (before the result parsing continues), clear it with `state.active_proc = None` so the registry never points at a dead proc during the `RETRY_DELAY` sleep. In the existing `except KeyboardInterrupt` branch, replace the bare `proc.kill(); proc.wait()` with a call to `kill_active_child()` (which group-kills and clears the registry) so a single Ctrl+C that lands inside the `for line in proc.stdout` loop also takes down the whole group; keep the existing session-id print and `sys.exit(130)`.

### Phase 3: Force-quit wiring

- [x] **Task 4: Kill the child on force-quit in the SIGINT handler** (depends on Task 2)
  Files: `orchestrator/main.py`
  Import `kill_active_child` from `.agents` (add it to the existing `from .agents import ...` line). In `_handle_sigint`, inside the force-quit branch (`if state.stop_requested:`), after printing `">>> Force quit."` and before `sys.exit(1)`, call `kill_active_child()`. Leave the first-SIGINT graceful path (`state.stop_requested = True` + "Will stop after the current milestone finishes") unchanged.
