# Sleep prevention survives a soft stop and ends with the orchestrator

**Date:** 2026-10-09
**Source:** the defect report relayed from tradeoxy_core on 2026-10-09 — a plan review that took far longer than its work, its connection lost each time the machine slept after a Ctrl+C — and the user's go in chat

Governing spec: [fault-handling.md](../../../docs/concepts/fault-handling.md) — the row "An operator stopping the run".

## What is true now

`_with_caffeinate(func, *args, **kwargs)` in `orchestrator/runtime.py` wraps a whole run; `main.py` calls it around `_implement_loop` and `_test_loop`. It starts sleep prevention with `subprocess.Popen(["caffeinate", "-ims"])` and no further options, so `caffeinate` joins the orchestrator's own process group. Around that spawn:

- `except FileNotFoundError` (no `caffeinate`, a non-macOS machine) runs `func` directly, prints `>>> Ran for … before stopping.` and re-raises if `func` raises, and returns the formatted elapsed time.
- Otherwise `func` runs in a `try`; `except Exception` prints the same `Ran for` line and re-raises; a `finally` sends `SIGTERM` to the `caffeinate` process and waits for it. The formatted elapsed time is returned.

`_run_claude` in `orchestrator/agents.py` starts each agent with `start_new_session=True`, so an agent is outside the terminal's foreground group; `caffeinate` is not.

A terminal Ctrl+C sends `SIGINT` to the whole foreground group. `_handle_sigint` in `runtime.py` handles it for the orchestrator: the first press only sets `state.stop_requested` and prints that the run stops after the current task, so the task keeps running; the second press kills the active child, reports a forced quit and calls `sys.exit(1)`. `caffeinate` has no handler, so the first press ends it, and nothing starts it again. The rest of the task runs with no sleep prevention, and the machine can sleep under it.

## What must be true after

**The spawn.** `_with_caffeinate` starts `caffeinate -ims -w <pid>`, where `<pid>` is the orchestrator's own process id (`os.getpid()`), with `start_new_session=True`. A `SIGINT` sent to the terminal's group does not reach it, and it exits by itself when the orchestrator's process exits, a forced kill included. The `FileNotFoundError` fallback and the `finally` cleanup stay as they are. `runtime.py` imports `os`.

**The test**, in `tests/test_runtime.py`: while the function wrapped by `_with_caffeinate` runs, a `SIGINT` delivered to the run's own process group leaves the sleep-prevention process alive. Real `caffeinate` exists only on macOS, so the test replaces the command with a long-lived stand-in and keeps every other option of the spawn, `start_new_session=True` included. The delivery reaches only the processes of the run under test; the test runner's own process and its parent are not ended by it. The failure is silent: the run carries on while the machine sleeps, and nothing else in the suite would notice.

**Behaviour.** The only change is that sleep prevention lasts through a soft stop and ends with the orchestrator's process, however that process ends.

## What breaks on contact

- `runtime.py` gains `import os`.
- The existing `_with_caffeinate` tests replace `subprocess.Popen` with a `Mock` and assert the `Ran for … before stopping.` output, the return value and the `SIGTERM` cleanup on the returned handle; none asserts the spawn's arguments, so they are unaffected.
- A second Ctrl+C still ends the run through `sys.exit(1)`; the `finally` cleanup still stops `caffeinate` on that path.
