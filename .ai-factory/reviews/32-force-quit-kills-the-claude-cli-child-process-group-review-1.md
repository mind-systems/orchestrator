# Code Review: Force-quit kills the Claude CLI child process group

Reviewed: `orchestrator/state.py`, `orchestrator/agents.py`, `orchestrator/main.py` (full files + `git diff HEAD`).

## Correctness analysis

The change matches the plan and the spec note, and the control flow is sound:

- **`state.py`** — `from __future__ import annotations` makes the `subprocess.Popen | None` annotation a deferred string (safe on the interpreter), and `subprocess` is also imported at runtime for the type reference. No issue.

- **`kill_active_child()`** — Checks `proc.poll() is not None` *before* `os.getpgid`/`os.killpg`. This is the critical safety property: `poll()` reaps the child via `waitpid`, so after it returns non-`None` the PID may be recycled; the early return avoids ever sending `SIGKILL` to a recycled PID/group. The `killpg` is correctly guarded against `ProcessLookupError`/`PermissionError` with a `proc.kill()` fallback, and the inner `proc.kill()` is itself wrapped so it can't raise out of the helper. The registry is cleared on every exit path. Correct.

- **`os.killpg(os.getpgid(proc.pid), SIGKILL)`** — Because `_run_claude` spawns with `start_new_session=True`, the child is its own group leader, so the group is addressable via the leader PID and killing the group reaps any grandchildren the CLI spawned. Matches intent.

- **Registry lifecycle in `_run_claude`** — `state.active_proc = proc` is set immediately after `Popen`; `state.active_proc = None` is set immediately after the normal `proc.wait()`, i.e. *before* the retryable `time.sleep(RETRY_DELAY)`, before the `returncode != 0` / `RateLimitError` / `RuntimeError` raises, and before `return`. So during the retry backoff the registry never points at a dead proc — exactly the race the spec called out. On retry, a fresh `proc` is re-registered. Correct.

- **Signal-handler concurrency** — `_handle_sigint` is installed via `signal.signal`, so Ctrl+C invokes the handler rather than raising `KeyboardInterrupt`. CPython runs signal handlers synchronously on the main thread between bytecodes; `_run_claude` runs its single child on that same main thread. There is therefore no concurrent reader/writer of `state.active_proc` — no TOCTOU between `poll()` and `getpgid()`, no race on the registry slot.

- **Force-quit teardown** — Second SIGINT (with `stop_requested` already set) calls `kill_active_child()` then `sys.exit(1)`. `SystemExit` propagates through `_run_claude`'s `try` (which catches only `KeyboardInterrupt`), is *not* swallowed by `_with_caffeinate`'s `except Exception` (SystemExit derives from BaseException), and caffeinate is still torn down by that function's `finally`. Clean exit. Correct.

- **`KeyboardInterrupt` branch** — Replacing `proc.kill(); proc.wait()` with `kill_active_child()` upgrades the single-Ctrl+C-in-loop path to a group kill and clears the registry. First-SIGINT graceful path and `start_new_session=True` are unchanged, per spec.

## Non-blocking observations (not defects, no action required)

- The `KeyboardInterrupt` branch no longer calls `proc.wait()` after the kill (the old code did). This can briefly leave a zombie, but `sys.exit(130)` follows immediately and the OS reaps on interpreter exit — negligible, and this branch is effectively only reachable before the SIGINT handler is installed.
- `import signal` was inserted between `import os` and `import shutil`, so the import block is no longer strictly alphabetical. Pure style; harmless.
- A non-`KeyboardInterrupt` exception raised inside the `for line in proc.stdout` loop would propagate without clearing `state.active_proc` or killing the child. This is pre-existing behavior (the prior code only handled `KeyboardInterrupt`), out of scope for this milestone, and does not regress.

No correctness, security, or runtime-breaking issues found.

REVIEW_PASS
