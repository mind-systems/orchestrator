# Plan: 27.1 — sleep prevention survives a soft stop and ends with the orchestrator

## Context
`_with_caffeinate` in `orchestrator/runtime.py` spawns `caffeinate -ims` in the orchestrator's own process group, so a terminal Ctrl+C kills it while `_handle_sigint`'s first press lets the task keep running — the rest of the task runs with the machine free to sleep. Per the task spec (`.ai-factory/specs/trickster77777/0063-sleep-prevention-survives-a-soft-stop.md`) and the governing spec `docs/concepts/fault-handling.md` (row "An operator stopping the run": a soft stop lets the current task finish "with the machine kept awake until it has"), `caffeinate` is started as `caffeinate -ims -w <os.getpid()>` in its own session, so a group SIGINT does not reach it and it exits by itself when the orchestrator's process ends, a forced kill included.

## Settings
- Testing: yes (one test pinned by the task spec — the failure is silent)
- Logging: minimal
- Docs: no (`docs/concepts/fault-handling.md` already states the behaviour)

## Tasks

### Sleep prevention outside the run's process group

- [x] **Spawn caffeinate in its own session, tied to the orchestrator's pid**
  Files: `orchestrator/runtime.py`
  Add `import os` to the stdlib imports (alphabetical, before `import signal`). In `_with_caffeinate`, change the spawn to:
  ```python
  caffeinate = subprocess.Popen(
      ["caffeinate", "-ims", "-w", str(os.getpid())],
      start_new_session=True,
  )
  ```
  `start_new_session=True` mirrors how `_run_claude` in `orchestrator/agents.py` already starts each agent outside the terminal's foreground group. `-w <pid>` makes `caffeinate` exit on its own when the orchestrator's process exits, however it ends. Everything else stays exactly as it is: the `except FileNotFoundError` fallback (run `func` directly, print `>>> Ran for … before stopping.` and re-raise on exception, return the formatted elapsed time), the `except Exception` print-and-re-raise, and the `finally` that sends `SIGTERM` and `wait()`s. Optionally update the comment/docstring only if it now reads inaccurately; do not touch `_handle_sigint`.

  Guards: the existing `_with_caffeinate` tests mock `subprocess.Popen` and do not assert its arguments, so they stay green unchanged. A second Ctrl+C still exits via `sys.exit(1)` and the `finally` still terminates `caffeinate` on that path.

### Test

- [x] **Pin that a SIGINT to the run's group leaves sleep prevention alive** (depends on Spawn caffeinate in its own session, tied to the orchestrator's pid)
  Files: `tests/test_runtime.py`
  Add one test, e.g. `test_with_caffeinate_survives_sigint_to_run_group`, after the existing `_with_caffeinate` tests. Do not add a `# Task N:` divider; if a section comment is added, it names the behaviour (e.g. `# _with_caffeinate — sleep prevention survives a soft stop`).

  The SIGINT must reach only the run under test, never pytest or its parent, so the scenario runs in a child Python process started in its own session:
  - The test launches `subprocess.run([sys.executable, "-c", SCRIPT], cwd=<repo root, i.e. Path(__file__).resolve().parent.parent>, start_new_session=True, capture_output=True, text=True, timeout=30)` and asserts `returncode == 0` (include `stdout`/`stderr` in the assertion message for diagnosis). Add `import subprocess`, `import sys` and `from pathlib import Path` to the test file's imports as needed.
  - `SCRIPT` (a module-level string constant or `textwrap.dedent` block) does, inside the child:
    1. `import os, signal, subprocess, sys`; `from orchestrator import runtime`.
    2. Installs `signal.signal(signal.SIGINT, runtime._handle_sigint)`, as `main.py` does around `_with_caffeinate`, so the child survives the first SIGINT exactly as a soft stop.
    3. Replaces `runtime.subprocess.Popen` with a wrapper that swaps only the command for a long-lived stand-in and forwards every keyword argument unchanged to the real `subprocess.Popen` (so `start_new_session=True` is kept), recording the returned process — e.g. stand-in `[sys.executable, "-c", "import time; time.sleep(60)", *args[1:]]` (the original `-ims -w <pid>` tail rides along as harmless argv). Real `caffeinate` exists only on macOS, which is why the command is substituted.
    4. Calls `runtime._with_caffeinate(func)` where `func`: sends `os.killpg(os.getpgrp(), signal.SIGINT)` to the child's own group; then waits on the recorded stand-in with `proc.wait(timeout=2)` — if it returns (the stand-in died), record failure; on `subprocess.TimeoutExpired` (still alive), record success. Allow a brief moment for the stand-in to start before sending the signal if needed (e.g. `time.sleep(0.5)`), so the check does not race process start-up.
    5. After `_with_caffeinate` returns (its `finally` sends SIGTERM to the stand-in and waits — cleanup stays exercised), exits `0` on success, non-zero with a message on `stderr` on failure.
  - Docstring states the behaviour: a SIGINT delivered to the run's own process group while the wrapped function runs leaves the sleep-prevention process alive.

  The test must fail against the old spawn (stand-in in the child's group dies on the SIGINT) and pass against the new one. Run `uv run pytest tests/test_runtime.py` and then the full `uv run pytest` to confirm.
