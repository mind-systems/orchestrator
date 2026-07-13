# Test Plan: Runtime lifecycle tests — elapsed formatting, caffeinate degrade, sigint

## Context
`orchestrator/runtime.py` has `_run_summary` covered but leaves `_fmt_elapsed`, `_with_caffeinate`, and `_handle_sigint` untested — including the non-macOS caffeinate degrade path and the hour-boundary format, both of which fail silently on regression. This plan adds net-new coverage for those three free functions, extending the existing save/restore-via-try/finally pattern already used by the `_run_summary` tests.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/ -v`

## Target Spec File
`tests/test_runtime.py`

## Tasks

### Phase 1: `_fmt_elapsed` — pure formatting

- [x] **Task 1: `_fmt_elapsed(seconds)` — format branches and hour boundary**
  Files: `tests/test_runtime.py`
  Import: `from orchestrator.runtime import _fmt_elapsed`. Pure function, no mocking — call directly with `int` seconds.
  Test cases:
  - `should return "Xm Ys" format when seconds is under one hour` — e.g. `_fmt_elapsed(125) == "2m 5s"` (no-hours branch, `hours == 0` is falsy)
  - `should return "Xh Ym Zs" format when seconds is one hour or more` — e.g. `_fmt_elapsed(3661) == "1h 1m 1s"` (hours branch: `divmod(3661,60)=(61,1)`, `divmod(61,60)=(1,1)`)
  - `should return "0m 0s" when seconds is 0` — `_fmt_elapsed(0) == "0m 0s"` (hours branch not taken)
  - `should format "59m 59s" without hours at the 3599 lower boundary` — `_fmt_elapsed(3599) == "59m 59s"` (`divmod(3599,60)=(59,59)`, `hours=0`)
  - `should format "1h 0m 0s" at the exact 3600 hour boundary` — `_fmt_elapsed(3600) == "1h 0m 0s"` (`divmod(3600,60)=(60,0)`, `divmod(60,60)=(1,0)`, `hours=1`); pins the exact divmod boundary against an off-by-one in the branch condition

### Phase 2: `_with_caffeinate` — degrade path and cleanup semantics

- [x] **Task 2: `_with_caffeinate(func, *args, **kwargs)` — success paths (caffeinate unavailable vs available)**
  Files: `tests/test_runtime.py`
  Import: `from orchestrator.runtime import _with_caffeinate`. Monkeypatch `orchestrator.runtime.subprocess.Popen`. For deterministic elapsed assertions, optionally monkeypatch `orchestrator.runtime.time.monotonic` with a fixed `side_effect` list (e.g. `[0.0, 1.0]`); otherwise assert only the shape of the returned string (regex `r"^\d+m \d+s$"` or `r"^(\d+h )?\d+m \d+s$"`) plus side effects.
  Test cases:
  - `should run func directly and return formatted elapsed when caffeinate is unavailable (FileNotFoundError branch)` — monkeypatch `Popen` to raise `FileNotFoundError`; pass a no-arg callable (e.g. `Mock()`); assert `func` called exactly once and the return value matches the `_fmt_elapsed` string shape. This is the non-macOS degrade path.
  - `should wrap func with a caffeinate Popen + SIGTERM cleanup and return formatted elapsed when caffeinate is available and func succeeds` — monkeypatch `Popen` to return a fake process (`Mock(spec=["send_signal", "wait"])`); pass a succeeding `func`; assert `func` called, the fake process's `send_signal` called with `signal.SIGTERM`, `wait()` called (finally cleanup runs on success too), and return value matches the `_fmt_elapsed` string shape

- [x] **Task 3: `_with_caffeinate` — exception propagation on both branches and cleanup on failure**
  Files: `tests/test_runtime.py`
  Use `capsys` to assert the printed message; `pytest.raises(ValueError, match="boom")` for propagation. The two `except Exception: ... print(...); raise` blocks are textually separate code (no shared helper) — cover each independently.
  Test cases:
  - `should re-emit "Ran for ... before stopping." and re-raise when func raises and caffeinate is unavailable` — monkeypatch `Popen` to raise `FileNotFoundError`; pass a `func` raising `ValueError("boom")`; assert the `ValueError` propagates and stdout contains `"Ran for"` and `"before stopping."`
  - `should re-emit "Ran for ... before stopping." and re-raise when func raises and caffeinate is available` — monkeypatch `Popen` to return a fake process; pass a `func` raising `ValueError("boom")`; assert the `ValueError` propagates and stdout contains the same message (independent code path from the FileNotFoundError branch)
  - `should still call caffeinate.send_signal(SIGTERM) and wait() (finally cleanup) when func raises and caffeinate is available` — same setup as the available-branch failure case; additionally assert the fake process's `send_signal` was called with `signal.SIGTERM` and `wait()` was called, pinning finally-block cleanup on the exception path

### Phase 3: `_handle_sigint` — Ctrl+C escalation

- [x] **Task 4: `_handle_sigint(sig, frame)` — first Ctrl+C sets stop_requested without exiting**
  Files: `tests/test_runtime.py`
  Import: `from orchestrator.runtime import _handle_sigint`; `from orchestrator import state`. Save/restore `state.stop_requested` (and any other `state.*` touched) via try/finally. Do not wrap in `pytest.raises` — an unexpected `SystemExit` should fail the test loudly.
  Test cases:
  - `should set state.stop_requested to True and print a warning without exiting on first Ctrl+C` — set `state.stop_requested = False`; call `_handle_sigint(signal.SIGINT, None)`; assert `state.stop_requested is True` afterward and (via `capsys`) stdout contains `"Will stop after the current milestone finishes."`; function returns normally (no `SystemExit`)

- [x] **Task 5: `_handle_sigint` — second Ctrl+C force-quits, with and without the notify guard**
  Files: `tests/test_runtime.py`
  Save/restore `state.stop_requested`, `state.config`, `state.project_dir` via try/finally. Monkeypatch `orchestrator.runtime.kill_active_child` and `orchestrator.runtime.notify` with `Mock()`s (patch the bound names in `runtime`, not the origin modules). Wrap every second-Ctrl+C call in `with pytest.raises(SystemExit)` — `SystemExit` is a `BaseException`. Cover each half of the `state.config is not None and state.project_dir is not None` guard independently (a wrong `or`/`and` would only be caught by exercising both).
  Test cases:
  - `should call kill_active_child, send a force-quit notify, and sys.exit(1) on second Ctrl+C when state.config and state.project_dir are both set` — set `state.stop_requested = True`, `state.config = <non-None sentinel/Mock>`, `state.project_dir = <Mock with a .name attribute>`; call inside `pytest.raises(SystemExit)`; assert exit code is 1, `kill_active_child` called once, and `notify` called once with `state.config`, a message containing `"force-quit"` and `state.project_dir.name`, and alert type `"stop"`
  - `should call kill_active_child and sys.exit(1) WITHOUT notifying when state.config is None` — set `state.stop_requested = True`, `state.config = None`, `state.project_dir = <set>`; call inside `pytest.raises(SystemExit)`; assert exit code is 1, `kill_active_child` called, and `notify` never called
  - `should call kill_active_child and sys.exit(1) WITHOUT notifying when state.project_dir is None` — set `state.stop_requested = True`, `state.config = <set>`, `state.project_dir = None`; call inside `pytest.raises(SystemExit)`; assert exit code is 1, `kill_active_child` called, and `notify` never called
