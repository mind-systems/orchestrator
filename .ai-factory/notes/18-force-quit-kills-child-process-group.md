# Force-quit kills the Claude CLI child process group

**Date:** 2026-06-23
**Source:** conversation context

## Key Findings

- A double Ctrl+C ("Force quit") leaves the running `claude -p` child alive; it keeps working in its own session and burns usage quota after the orchestrator has exited.
- Root cause is two-fold: (1) the second SIGINT is handled by `_handle_sigint` in `main.py`, which calls `sys.exit(1)` → raises `SystemExit`, which is **not** caught by the `except KeyboardInterrupt` in `_run_claude` (`agents.py`), so its `proc.kill()` cleanup never runs; (2) the child is spawned with `start_new_session=True`, making it a session/process-group leader, so the terminal's Ctrl+C (SIGINT to the foreground group) never reaches it directly.
- The same orphan mechanism affects every agent, not just the implementer — killing the orchestrator mid-planning still leaves the planner child running, which is why a plan file appears on disk after the orchestrator was force-quit.
- Fix: register the active `Popen` so the SIGINT handler can reach it, and on force-quit send `SIGKILL` to the **whole process group** (`os.killpg(os.getpgid(proc.pid), SIGKILL)`) before `sys.exit`.

## Details

### Current state

- `orchestrator/agents.py` — `_run_claude()` spawns `proc = subprocess.Popen(cmd, ..., start_new_session=True)` (around line 114). The only child cleanup is inside `except KeyboardInterrupt:` (`proc.kill(); proc.wait()`), reached only when a *KeyboardInterrupt* propagates into the `for line in proc.stdout` loop.
- `orchestrator/main.py` — `_handle_sigint(sig, frame)` (around line 21): first SIGINT sets `state.stop_requested = True` and prints "Will stop after the current milestone finishes"; second SIGINT prints "Force quit." and calls `sys.exit(1)`. It has no reference to the running child, so it cannot kill it.
- `orchestrator/state.py` — currently holds only `stop_requested: bool`.

Because the force-quit path raises `SystemExit` from inside the signal handler (running on the main thread, interrupting the blocking `for line in proc.stdout`), it bypasses the `except KeyboardInterrupt` entirely. The interpreter tears down and the group-leader child is reparented to init, still running.

### The change

1. **`orchestrator/state.py`** — add an `active_proc: subprocess.Popen | None = None` registry (with `from __future__ import annotations` + `import subprocess` for the type). This is the single in-flight child; `_run_claude` runs one at a time on the main thread, so one slot is enough.

2. **`orchestrator/agents.py`**:
   - Add `import signal`.
   - Add a module-level `kill_active_child()` helper: read `state.active_proc`; if `None` or already exited (`proc.poll() is not None`) return; else `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` guarded by `try/except (ProcessLookupError, PermissionError)` falling back to `proc.kill()`; then set `state.active_proc = None`. Killing the group (not just the direct PID) also reaps any grandchildren the CLI spawned.
   - In `_run_claude`, right after `Popen(...)`, set `state.active_proc = proc`. Clear it (`state.active_proc = None`) after the run finishes — after the normal `proc.wait()` and in the `except KeyboardInterrupt` branch — so that during the `RETRY_DELAY` sleep the registry does not point at a dead proc.
   - In the existing `except KeyboardInterrupt` branch, replace bare `proc.kill()` with the same group-kill (call `kill_active_child()` or inline `os.killpg`) so a single Ctrl+C that *does* land in the loop also takes down the group.

3. **`orchestrator/main.py`** — in `_handle_sigint`, in the force-quit branch (`if state.stop_requested:`), call `kill_active_child()` (imported from `.agents`) **before** `sys.exit(1)`, after printing "Force quit.".

### Guards / gotchas

- `os.getpgid` / `os.killpg` raise `ProcessLookupError` if the child already exited (e.g. force-quit lands during the retry `time.sleep`) — must be caught; this is why `active_proc` is cleared right after `proc.wait()`.
- Use `SIGKILL` (not `SIGTERM`) on force-quit: the user's explicit intent is "must not keep working" — no graceful window.
- Do **not** change the first-SIGINT behaviour (graceful "stop after current milestone"); only the second/force-quit path kills the child.
- Keep `start_new_session=True` — it is what makes the whole group addressable via the leader PID; the fix relies on it rather than removing it.

### How to verify

- Start `uv run orchestrator implement <project>`; once a `[session: ...]` line prints, press Ctrl+C twice.
- After the orchestrator exits, `ps aux | grep "claude -p"` shows **no** surviving child for that run (previously the `claude -p ... Implement the plan` process stayed alive for tens of minutes).
- Repeat during the planning phase (before implement) to confirm the planner child is also reaped and no stray plan file is produced after force-quit.

## Open Questions

- Whether a no-output watchdog/timeout in `_run_claude` (separate concern) should be added so an API-side stall converts to a retry instead of an indefinite hang — tracked separately, out of scope for this task.
