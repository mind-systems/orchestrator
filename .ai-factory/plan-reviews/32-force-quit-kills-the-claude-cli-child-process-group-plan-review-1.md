# Plan Review: Force-quit kills the Claude CLI child process group

**Plan:** `32-force-quit-kills-the-claude-cli-child-process-group.md`
**Risk Level:** 🟢 Low

## Verification Against Codebase

I read `state.py`, `agents.py`, and `main.py` in full and cross-checked every claim in the plan. The plan is accurate and faithful to both the ROADMAP milestone (line 81) and the spec note (`.ai-factory/notes/18-force-quit-kills-child-process-group.md`).

Confirmed against the actual code:

- **`state.py`** currently holds only `stop_requested: bool = False` and has no imports — the plan's additions (`from __future__ import annotations`, `import subprocess`, `active_proc`) are correct and non-conflicting.
- **`agents.py` line 120** — `subprocess.Popen(..., start_new_session=True)` is confirmed, so the child is a process-group leader and `os.getpgid(proc.pid) == proc.pid`. `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` is the correct way to take down the whole group. `os` is already imported (line 6); `signal` is not, so the added `import signal` is needed.
- **`agents.py` lines 139–146** — the `except KeyboardInterrupt` branch with `proc.kill(); proc.wait()` and `sys.exit(130)` exists exactly as described; replacing the kill with `kill_active_child()` is valid.
- **`agents.py` line 148** — `proc.wait()` is the correct anchor point for clearing `state.active_proc = None` before the `RETRY_DELAY` sleep / result parsing. The retryable `continue` (lines 176–179) and all later raises occur after this clear, so the registry never points at a dead proc during the sleep.
- **`main.py` line 13** — the `from .agents import ...` line exists and is the right place to add `kill_active_child`.
- **`main.py` lines 21–27** — `_handle_sigint` matches the plan: force-quit branch (`if state.stop_requested:`) prints `">>> Force quit."` then `sys.exit(1)`. Inserting `kill_active_child()` before `sys.exit(1)` is the correct fix for the actual root cause.

The root-cause analysis is correct: with the custom SIGINT handler installed, the second Ctrl+C raises `SystemExit` from inside `_handle_sigint`, which the `except KeyboardInterrupt` in `_run_claude` does not catch — so the group-leader child is orphaned. Task 4 is the load-bearing fix; Tasks 1–3 provide the registry it needs.

## Correctness Notes (non-blocking)

- **`kill_active_child()` early-return ordering is sound.** After `proc.wait()`, `proc.poll()` returns a non-`None` returncode, so the helper returns early and never calls `os.getpgid` on a reaped PID (which would raise `ProcessLookupError`). The `try/except (ProcessLookupError, PermissionError)` additionally covers the race where the child exits between the `poll()` check and the `killpg` call. Good defense in depth.
- **Signal-handler safety.** `os.getpgid` / `os.killpg` are safe to invoke from a Python signal handler (handlers run on the main thread between bytecode ops). No async-signal-safety concern here.

## Minor Observations (informational, no change required)

1. **`import subprocess` in `state.py` is unused at runtime.** With `from __future__ import annotations`, the `active_proc: subprocess.Popen | None` annotation is a string and never evaluated. The import is harmless and aids type-checker/reader clarity — the spec explicitly requests it, so keep it. A linter may flag it as unused; that is expected.
2. **Name shadowing heads-up.** `agents.py` already defines `_has_signal(text: str, signal: str)`, whose `signal` parameter shadows the new module-level `import signal` *within that function only*. `_has_signal` does not use the module, so there is no conflict — but the implementer should not be alarmed by the duplicate name.
3. **The `except KeyboardInterrupt` edit (Task 3) is defensive hardening, not the primary fix.** Because `run_implement`/`run_test` install `_handle_sigint` before running, a terminal Ctrl+C dispatches to the handler rather than raising `KeyboardInterrupt`, so this branch is rarely hit in normal CLI use. Routing it through `kill_active_child()` is still correct and worthwhile for any path where the default handler is active. No action needed.

## Context Gates

- **Architecture (`ARCHITECTURE.md`):** WARN — none. `ARCHITECTURE.md` documents `state.py` as a global-flag module importable from any layer (lines 24, 44). Adding `active_proc` alongside `stop_requested` is consistent with that role and the existing dependency rules. No boundary violation.
- **Rules (`RULES.md`):** Not present — skipped (WARN, non-blocking).
- **Roadmap (`ROADMAP.md`):** Aligned. The plan maps 1:1 to milestone line 81 and the referenced spec note `.ai-factory/notes/18-...md`. Scope is respected: first-SIGINT graceful stop unchanged, `start_new_session=True` kept, `SIGKILL` (not `SIGTERM`) used on force-quit. The out-of-scope no-output watchdog from the note's Open Questions is correctly excluded.
- **Skill-context (`.ai-factory/skill-context/aif-review/SKILL.md`):** Not present — no project-specific overrides to apply.

## Positive Notes

- Tasks are correctly ordered with explicit dependencies (Task 2 → 3, 4) and each names the exact file and insertion point.
- The plan anticipates the two real races (force-quit during `RETRY_DELAY` sleep; child exiting before `killpg`) and addresses both with the `active_proc = None` clear and the `ProcessLookupError` guard.
- Verification strategy in the spec (`ps aux | grep "claude -p"` after double Ctrl+C, during both implement and plan phases) gives a concrete pass/fail signal.

The plan is complete, technically correct, and ready for implementation.

PLAN_REVIEW_PASS
