## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/runtime.py`, `tests/test_runtime.py`). The plan, its sidecar and the plan review are pipeline artifacts and were read only for context.
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap / task spec**: OK. The diff matches the contract line for 27.1 in `.ai-factory/roadmaps/trickster77777.md` and the spec `.ai-factory/specs/trickster77777/0063-sleep-prevention-survives-a-soft-stop.md` on each point:
  - It adds `import os`.
  - The spawn is `["caffeinate", "-ims", "-w", str(os.getpid())]` with `start_new_session=True`.
  - The `FileNotFoundError` fallback, the `except Exception` print-and-re-raise, and the `finally` SIGTERM plus `wait()` are unchanged.
  - It adds exactly one new test in `tests/test_runtime.py`.
- **Governing spec**: OK. `docs/concepts/fault-handling.md`, row "An operator stopping the run", says a soft stop lets the current task finish "with the machine kept awake until it has". The code now does this. No doc needs to change.
- **Architecture**: OK. The change stays inside `runtime.py`, the module that owns the process lifecycle according to `.ai-factory/ARCHITECTURE.md`. It adds no new dependencies.
- **Rules**: WARN (non-blocking). `.ai-factory/RULES.md` does not exist. The global rules are met: the new docstring and section comment describe behaviour, cite no plan layer, and add no `# Task N:` divider.

### Verification

- `uv run pytest`: 224 passed.
- Regression check: I restored the old `runtime.py` (`Popen(["caffeinate", "-ims"])`) temporarily, and `test_with_caffeinate_survives_sigint_to_run_group` **fails**. Then I put the new code back and restaged it. So the test catches the silent failure the spec describes.
- Second Ctrl+C: `sys.exit(1)` raises `SystemExit`, which bypasses `except Exception` and still runs the `finally`, so `caffeinate` is still terminated.
- Forced kill: `-w <pid>` makes `caffeinate` exit when the orchestrator's pid exits. Under `uv run`, that pid is the Python orchestrator process itself.
- Signal isolation in the test:
  - The child runs with `start_new_session=True`, so `os.killpg(os.getpgrp(), SIGINT)` reaches only the child's own group, never pytest or its parent.
  - The child installs `_handle_sigint`, so it survives the press as a soft stop, just as `main.py` sets things up before `_with_caffeinate`.
- Fidelity of the stand-in: `fake_popen` swaps only the command and forwards every keyword argument to the real `subprocess.Popen`, so `start_new_session=True` is what the test actually exercises. On the failing path, `send_signal` on an already-reaped process is a no-op, so the `finally` cannot raise there.
- The existing `_with_caffeinate` tests mock `Popen` without asserting its arguments, so they are unaffected.

### Critical Issues

None.

### Positive Notes

- The test sends a real signal to a real process group inside an isolated session. It guards the behaviour, not the spelling of the `Popen` arguments, and it runs on non-macOS machines because only the command is substituted.
- The new section comment names the behaviour instead of a task coordinate.
- The docstring states why the spawn has its shape (its own session, `-w` lifetime) in present tense, with no change history.
- The diff is minimal: `_handle_sigint` and the fallback/cleanup paths are untouched.

REVIEW_PASS
