## Plan Review Summary

**Files Reviewed:** 1 plan (`28-runtime-lifecycle-tests-...md`) against `orchestrator/runtime.py`, `orchestrator/state.py`, `orchestrator/notify.py`, existing `tests/test_runtime.py`, spec `.ai-factory/specs/19-runtime-lifecycle.md`, and roadmap line in `ROADMAP_TESTS.md`.
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): the plan respects the project's deliberate module-global state pattern — it reuses the save/restore-via-try/finally discipline already established by the `_run_summary` tests rather than proposing a DI refactor. The spec explicitly defers that refactor as out of scope; the plan honors that. No boundary violation. **PASS.**
- **Rules** (`.ai-factory/RULES.md`): not present — gate skipped, no ERROR.
- **Roadmap** (`ROADMAP_TESTS.md`): the `[ ]` milestone "Runtime lifecycle tests — elapsed formatting, caffeinate degrade, sigint" (`tests/test_runtime.py`, `Spec: .ai-factory/specs/19-runtime-lifecycle.md`) maps 1:1 onto the plan. All 8 spec test cases (1–4, 5–8, 9–11) are present in the plan's 5 tasks, with no scope drift and nothing dropped. **PASS.**
- **Skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): not present — no project overrides to apply.
- **Test philosophy**: the three targeted functions are genuinely silent-failure surfaces (mis-formatted elapsed string, wrong caffeinate degrade branch, wrong sigint escalation) — correct fit for coverage, not loud-failure surfaces.

### Critical Issues
None.

### Correctness verification against source

Every concrete claim in the plan was checked against `runtime.py`:

- **`_fmt_elapsed` arithmetic** — all five cases are arithmetically correct against `divmod(seconds,60)` then `divmod(mins,60)` (`runtime.py:26–29`):
  - `125` → `(2,5)`,`(0,2)` → `"2m 5s"` ✓ (`hours==0` falsy → no-hours branch)
  - `3661` → `(61,1)`,`(1,1)` → `"1h 1m 1s"` ✓
  - `0` → `"0m 0s"` ✓
  - `3599` → `(59,59)`,`(0,59)` → `"59m 59s"` ✓
  - `3600` → `(60,0)`,`(1,0)` → `"1h 0m 0s"` ✓ (boundary pinned)
- **`_with_caffeinate` branch structure** matches `runtime.py:42–67`: the `FileNotFoundError` degrade path (`46–55`) and the caffeinate-available path with `try/except/finally` (`57–67`) are textually separate blocks with no shared helper — the plan correctly requires both exception paths (Tasks 3) and the `finally` cleanup (`send_signal(signal.SIGTERM)` + `wait()`) on both success and failure to be exercised independently. Monotonic-call counts per path are 2, so a `side_effect=[0.0, 1.0]` list is sufficient if used.
- **`_handle_sigint` escalation** matches `runtime.py:15–23`: first Ctrl+C sets `state.stop_requested=True` and prints (Task 4); second Ctrl+C calls `kill_active_child()`, guards the `notify(...)` on `state.config is not None and state.project_dir is not None`, and `sys.exit(1)` (Task 5). Both halves of the `and` guard are covered separately — the right call, since an `or`/`and` swap surfaces only when both halves are exercised. The notify message assertion (`"force-quit"`, `state.project_dir.name`, alert `"stop"`) matches the f-string at `runtime.py:20`.
- **Monkeypatch targets are correct**: `notify` and `kill_active_child` are bound by name into `runtime` (`from .notify import notify`, `from .agents import kill_active_child` at `runtime.py:11–12`), so the plan's instruction to patch `orchestrator.runtime.notify` / `orchestrator.runtime.kill_active_child` (not the origin modules) is right.
- **`SystemExit` handling**: the plan correctly wraps every second-Ctrl+C call in `pytest.raises(SystemExit)` (it is a `BaseException`) and correctly forbids wrapping the first-Ctrl+C call, so an unexpected exit fails loudly. Matches the spec's Gotchas.
- **State save/restore**: Task 5 saves/restores `state.stop_requested`, `state.config`, `state.project_dir`. `_run_summary()` (reached on the second-Ctrl+C notify path) reads `state.run_started` / `state.milestones_done` but does not mutate them, so omitting them from the restore list is safe. `kill_active_child` is mocked, so `state.active_proc` is untouched.

### Positive Notes
- The plan's per-case rationale (e.g. "pins the exact divmod boundary against an off-by-one") shows the coverage is targeted at real silent-regression risks, not line-count padding.
- Correctly identifies the two `except`/`print`/`raise` blocks as independent code paths requiring separate tests — a subtle point the spec's Gotchas also flags.
- Import paths, function signatures, and the `_fmt_elapsed` output shape regex all match source exactly.

### Implementer guidance (non-blocking, not a defect)
- For Task 5, when building `state.project_dir` as a Mock with a usable `.name`, note the classic trap: `Mock(name="proj").name` does **not** return `"proj"` (`name` is a reserved `Mock` constructor kwarg). Set it explicitly — `m = Mock(); m.name = "proj"` — so the `state.project_dir.name in <message>` containment assertion operates on a real string. The plan already specifies "a Mock with a `.name` attribute", so this is within the implementer's normal execution, not a plan gap.

PLAN_REVIEW_PASS
