## Plan Review Summary

**Plan:** 27.1 — sleep prevention survives a soft stop and ends with the orchestrator
**Files targeted:** `orchestrator/runtime.py`, `tests/test_runtime.py`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap** — OK. The plan matches the contract line for 27.1 in `.ai-factory/roadmaps/trickster77777.md` (Phase 27 — A soft stop keeps the machine awake). It also matches its task spec, `.ai-factory/specs/trickster77777/0063-sleep-prevention-survives-a-soft-stop.md`, on every point: the spawn `caffeinate -ims -w <os.getpid()>` with `start_new_session=True`, `import os`, the unchanged fallback and cleanup, and one test that substitutes the command but keeps the spawn options.
- **Governing spec** — OK. In `docs/concepts/fault-handling.md`, the "An operator stopping the run" row says a soft stop finishes the current task "with the machine kept awake until it has". The current code does not do this, and this plan closes that gap. `Docs: no` is correct: no other doc describes the spawn's arguments. `docs/future/run-context-refactor.md` and `.ai-factory/ARCHITECTURE.md` only name `_with_caffeinate` and `caffeinate`, and both stay accurate.
- **Architecture** — OK. The change stays inside `runtime.py`, the module that owns the process lifecycle according to ARCHITECTURE.md. It adds no new module boundaries or dependencies.
- **Rules** — WARN (non-blocking). `.ai-factory/RULES.md` does not exist, so this gate had nothing to check. The plan does follow the global "comments never cite the plan layer" rule: it explicitly forbids a `# Task N:` divider for the new test.

### Verification against the codebase

- `orchestrator/runtime.py`: `_with_caffeinate` currently spawns `subprocess.Popen(["caffeinate", "-ims"])` with no options. The file imports `signal`, `subprocess`, `sys` and `time`, but not `os`. The plan's import placement ("before `import signal`") is correct. The `FileNotFoundError` fallback, the `except Exception` print-and-re-raise and the `finally` SIGTERM plus `wait()` all match the plan's description.
- `orchestrator/agents.py`: `_run_claude` does use `start_new_session=True`, as the plan says it mirrors. `kill_active_child` uses `os.killpg` on the agent's group, which does not affect `caffeinate`.
- `orchestrator/main.py`: `signal.signal(signal.SIGINT, _handle_sigint)` is installed right before both `_with_caffeinate` calls (implement and test modes). The test script reproduces this setup.
- Existing tests: `tests/test_runtime.py` mocks `runtime.subprocess.Popen` and asserts only on `send_signal(SIGTERM)`, `wait()` and the return value or output. None of them checks the spawn arguments, so they stay green.
- Second Ctrl+C: `sys.exit(1)` raises `SystemExit`, which skips `except Exception` but still runs the `finally`, so `caffeinate` is still terminated. The behaviour is unchanged, as the plan says.
- Test mechanics:
  - The child runs with `start_new_session=True`, so `os.killpg(os.getpgrp(), SIGINT)` reaches only the child's own group, never pytest or its parent.
  - The child installs `_handle_sigint`, so it survives the first press with `state.stop_requested` set.
  - With the old spawn, the Python stand-in shares the child's group. It dies from `KeyboardInterrupt`, or from the default SIGINT action if the signal lands during interpreter start-up, so `wait(timeout=2)` returns and the test fails.
  - With the new spawn, the stand-in is in its own session, `wait` times out, and the test passes.
  - Neither outcome depends on start-up timing, so the test is not flaky.
  - `from orchestrator import runtime` in the child works because the project is installed into the venv that `sys.executable` points to under `uv run`, and the `cwd` is the repo root.
  - Importing `runtime`, and through it `notify` and `agents`, has no side effects at import time.
- `caffeinate -w <pid>` is the documented macOS option: it holds the assertions until that pid exits. Under `uv run`, `os.getpid()` is the Python orchestrator process itself, so a forced kill of that process also ends `caffeinate`.

### Critical Issues

None.

### Positive Notes

- The test sends the real signal to a real process group inside an isolated child session. This exercises the actual failure mode instead of asserting on mocked `Popen` arguments, so it guards the behaviour rather than the spelling.
- The command substitution keeps every keyword argument through the real `Popen`, so the test still checks `start_new_session=True` while running on non-macOS CI.
- The plan explicitly keeps the `finally` cleanup in play inside the test, and it requires the test to fail against the old spawn.
- The scope is tight: there are no changes to `_handle_sigint` and no doc churn.

PLAN_REVIEW_PASS
