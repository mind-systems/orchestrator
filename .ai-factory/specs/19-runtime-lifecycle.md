# Runtime Lifecycle — Test Plan

**Date:** 2026-07-13
**Source:** roadmap-test-coverage agent

## Source Overview

`orchestrator/runtime.py` (67 lines) owns the process-lifecycle plumbing around a run: formatting elapsed time (`_fmt_elapsed`), wrapping a long-running function with macOS sleep-prevention via `caffeinate` (`_with_caffeinate`), and handling Ctrl+C escalation from "graceful stop after this milestone" to "force quit now" (`_handle_sigint`). It reads/writes module-level flags in `orchestrator/state.py` (`stop_requested`, `config`, `project_dir`, `run_started`, `milestones_done`, `active_proc`) rather than taking them as parameters, and calls out to `notify()` (`orchestrator/notify.py`) and `kill_active_child()` (`orchestrator/agents.py`) on the force-quit path.

## Instantiation

- No class/object to instantiate — all three targets are free functions imported directly: `from orchestrator.runtime import _fmt_elapsed, _with_caffeinate, _handle_sigint`.
- `_fmt_elapsed`: pure function, call directly with an `int` seconds value — no mocking.
- `_with_caffeinate`: monkeypatch `subprocess.Popen` inside `orchestrator.runtime` (i.e. `monkeypatch.setattr(orchestrator.runtime.subprocess, "Popen", ...)`) to either return a fake Popen-like object (with `.send_signal` and `.wait` no-op methods) or raise `FileNotFoundError` to simulate the two branches. Optionally monkeypatch `time.monotonic` (module `orchestrator.runtime.time`) to make elapsed-time assertions deterministic instead of asserting on wall-clock-derived strings.
- `_handle_sigint`: monkeypatch `orchestrator.runtime.notify`, `orchestrator.runtime.kill_active_child`, and use `pytest.raises(SystemExit)` around the call rather than monkeypatching `sys.exit` (simpler and avoids masking real bugs). Set/reset `state.stop_requested`, `state.config`, `state.project_dir` around each test.
- Global state (`state.stop_requested`, `state.config`, `state.project_dir`, `state.run_started`, `state.milestones_done`, `state.active_proc`) must be saved before and restored after each test via `try/finally`, exactly matching the pattern already used in `test_run_summary_with_elapsed_and_count` / `test_run_summary_with_no_run_started`.

## Existing Coverage

Only `_run_summary` is tested today (2 tests: one with `run_started` set + a milestone count, one with `run_started is None`). `_fmt_elapsed`, `_with_caffeinate`, and `_handle_sigint` — the three functions this plan targets — have **zero** direct tests (confirmed via grep across `tests/`). Everything below is net-new coverage.

## Test Cases

### `_fmt_elapsed(seconds)`

1. **should return "Xm Ys" format when seconds is under one hour (no hours branch)**
   - Exercises: `_fmt_elapsed`
   - Setup: none — pure function. E.g. `_fmt_elapsed(125) == "2m 5s"`.

2. **should return "Xh Ym Zs" format when seconds is 3600 or more (hours branch — currently completely untested)**
   - Exercises: `_fmt_elapsed`
   - Setup: none. E.g. `_fmt_elapsed(3661) == "1h 1m 1s"` (3661 = 3600 + 61 = 1h 1m 1s via `divmod(3661, 60) = (61, 1)`, then `divmod(61, 60) = (1, 1)`).

3. **should handle 0 seconds**
   - Exercises: `_fmt_elapsed`
   - Setup: none. `_fmt_elapsed(0) == "0m 0s"` (hours branch not taken since `hours == 0` is falsy).

4. **should format the exact hour boundary correctly (3600 vs 3599)**
   - Exercises: `_fmt_elapsed`
   - Setup: none. Boundary check: `_fmt_elapsed(3599) == "59m 59s"` (just under the hours branch — `divmod(3599,60)=(59,59)`, `divmod(59,60)=(0,59)`, `hours=0` so no-hours format), while `_fmt_elapsed(3600) == "1h 0m 0s"` (`divmod(3600,60)=(60,0)`, `divmod(60,60)=(1,0)`, `hours=1` so hours format triggers). This pins the exact divmod boundary — an off-by-one in the branch condition would silently mis-format right at this line.

### `_with_caffeinate(func, *args, **kwargs)`

5. **should run func directly and return formatted elapsed when caffeinate is unavailable (FileNotFoundError branch)**
   - Exercises: `_with_caffeinate`
   - Setup: monkeypatch `orchestrator.runtime.subprocess.Popen` to raise `FileNotFoundError` when called with `["caffeinate", "-ims"]`. Pass a `func` that's a simple no-arg callable (e.g. a lambda or `Mock()`) that returns normally. Assert `func` was called exactly once, and the return value matches `_fmt_elapsed(...)` format (e.g. regex `r"^\d+m \d+s$"` or mock `time.monotonic` to return fixed before/after values for a deterministic string). This is the non-macOS degrade path — explicitly called out in the roadmap's first hardening task and still has zero direct test today.

6. **should wrap func with a caffeinate Popen + SIGTERM cleanup when caffeinate is available, and still return normally when func succeeds**
   - Exercises: `_with_caffeinate`
   - Setup: monkeypatch `Popen` to return a fake process object (e.g. `Mock(spec=["send_signal", "wait"])`) instead of raising. Pass a `func` that succeeds. Assert: `func` was called; the fake process's `send_signal` was called with `signal.SIGTERM`; `wait()` was called (i.e. the `finally` cleanup ran even on the success path, not just on exception); return value is the `_fmt_elapsed` string.

7a. **should re-raise func's exception after printing "Ran for X before stopping" — FileNotFoundError/no-caffeinate branch**
   - Exercises: `_with_caffeinate` (lines ~49-54, the `except FileNotFoundError` block's inner try/except)
   - Setup: monkeypatch `Popen` to raise `FileNotFoundError`. Pass a `func` that raises a distinct exception (e.g. `ValueError("boom")`). Assert: the original exception type/message propagates out of `_with_caffeinate` (`pytest.raises(ValueError, match="boom")`); use `capsys` to assert stdout contains `"Ran for"` and `"before stopping."`.

7b. **should re-raise func's exception after printing "Ran for X before stopping" — caffeinate-available branch**
   - Exercises: `_with_caffeinate` (lines ~57-62, the outer try/except/finally block)
   - Setup: monkeypatch `Popen` to return a fake process (success case, not raising). Pass a `func` that raises `ValueError("boom")`. Assert: exception propagates (`pytest.raises(ValueError, match="boom")`); stdout contains the same "Ran for ... before stopping." message. This is a **near-duplicate but independent code path** from 7a — the two `except Exception: ... print(...); raise` blocks are not shared code (no helper function), so passing 7a does not imply 7b is correct; both must be tested independently.

8. **should still call caffeinate.send_signal(SIGTERM)/wait() (finally-block cleanup) even when func raises, when caffeinate was available**
   - Exercises: `_with_caffeinate` (finally block, lines ~63-65)
   - Setup: same as 7b (fake Popen returned, `func` raises). In addition to asserting the exception propagates, assert the fake process's `send_signal(SIGTERM)` and `wait()` were both called — i.e. cleanup happens on the exception path too, not just on success (test 6 covers the success path; this covers the exception path so the `finally` semantics are pinned on both branches).

### `_handle_sigint(sig, frame)`

9. **should set state.stop_requested = True and print a warning without exiting, on first Ctrl+C**
   - Exercises: `_handle_sigint`
   - Setup: save/reset `state.stop_requested` via try/finally; set `state.stop_requested = False` before calling. Call `_handle_sigint(signal.SIGINT, None)`. Assert `state.stop_requested is True` afterward; assert (via `capsys`) stdout contains "Will stop after the current milestone finishes." Assert no `SystemExit` is raised (function returns normally) — do this by simply calling it without wrapping in `pytest.raises`, so an unexpected `SystemExit` would fail the test loudly.

10. **should call kill_active_child(), send a force-quit notify, and sys.exit(1) on second Ctrl+C when state.config and state.project_dir are both set**
    - Exercises: `_handle_sigint`
    - Setup: save/reset `state.stop_requested`, `state.config`, `state.project_dir` via try/finally. Set `state.stop_requested = True`, `state.config = <non-None sentinel/Mock>`, `state.project_dir = <Path or Mock with a .name attribute>`. Monkeypatch `orchestrator.runtime.kill_active_child` and `orchestrator.runtime.notify` with `Mock()`s. Call inside `with pytest.raises(SystemExit) as exc_info: _handle_sigint(signal.SIGINT, None)`. Assert `exc_info.value.code == 1`; assert `kill_active_child` was called once; assert `notify` was called once with `state.config`, a message containing `"force-quit"` and `state.project_dir.name`, and alert type `"stop"`.

11. **should call kill_active_child() and sys.exit(1) WITHOUT sending a notify when state.config or state.project_dir is None (guard condition)**
    - Exercises: `_handle_sigint`
    - Setup: same pattern as #10, but parametrize/duplicate for `state.config = None, state.project_dir = <set>` and `state.config = <set>, state.project_dir = None` (both halves of the `and` guard need independent coverage — a wrong guard, e.g. `or` instead of `and`, would only be caught by exercising both). Call inside `pytest.raises(SystemExit)`. Assert exit code is 1; assert `kill_active_child` was called; assert `notify` (mocked) was **never called** (`notify_mock.assert_not_called()`). This is the silent-failure-relevant case: if the guard were wrong, `notify` could either be called with `None` and crash on attribute access (e.g. `state.project_dir.name` on `None`), or (worse) silently fail to fire when it legitimately should — this test pins the guard's exact boolean behavior.

## Refactor Required

Testability review verdict: `_handle_sigint`, `_run_elapsed`, and `_run_summary` read/write `state.stop_requested`/`state.config`/`state.project_dir`/`state.run_started`/`state.milestones_done` as module-level globals rather than parameters, and `_run_elapsed`/`_with_caffeinate` call `time.monotonic()`/`subprocess.Popen` directly with no injectable clock/process abstraction.

Note: as with the sidecar-I/O area, the global-flag pattern is this project's deliberate, documented architecture (`.ai-factory/ARCHITECTURE.md`), and the existing `_run_summary` tests already establish a working save/restore-via-try/finally pattern for exactly these globals — the test cases in this note extend that same pattern to `_handle_sigint`/`_fmt_elapsed`/`_with_caffeinate` without difficulty. A DI-style refactor (signal handler registered as a closure capturing explicit state, or a small `RunContext` object threaded through instead of `state.py` globals) is possible but is an architecture change, not a prerequisite for writing the tests already scoped above. Flagging for the decomposition stage to weigh, not asserting it blocks testing.

## Gotchas

- **`sys.exit(1)` raises `SystemExit`, which is a `BaseException`, not `Exception`.** Every second-Ctrl+C test path must wrap the call in `with pytest.raises(SystemExit)`. Do NOT catch it with a bare `except Exception` in test helpers, and do not let it propagate uncaught — an uncaught `SystemExit` inside a test process can abort the pytest run itself.
- **Global state must be saved/restored via try/finally**, exactly as `test_run_summary_with_elapsed_and_count`/`test_run_summary_with_no_run_started` already do — `state.stop_requested`, `state.config`, and `state.project_dir` are process-global and leak across tests if not reset, which can cause spurious failures/passes in unrelated tests (e.g. a leaked `stop_requested = True` would silently flip a later "first Ctrl+C" test into the "second Ctrl+C" branch).
- **The two exception-handling paths in `_with_caffeinate` (lines ~49-54 inside the `FileNotFoundError` branch, and lines ~57-62 in the caffeinate-available branch) are near-duplicate but textually separate code** — there is no shared helper. Passing a test on one branch gives zero assurance about the other; both (test cases 7a/7b) must be exercised independently.
- **`time.monotonic()` non-determinism**: `_with_caffeinate` and `_fmt_elapsed` compute elapsed time from `time.monotonic()` deltas. Either (a) monkeypatch `orchestrator.runtime.time.monotonic` to return fixed, controlled values (e.g. a `side_effect` list `[0.0, 1.0]` for start/end) so the exact formatted string can be asserted, or (b) if not monkeypatched, only assert on the *shape* of the output (regex like `r"^\d+m \d+s$"`) and on side effects (mock calls), not on exact elapsed values.
- **Fake `Popen` replacement for `_with_caffeinate`** needs only `send_signal(sig)` and `wait()` methods (no real process) — a `unittest.mock.Mock()` (unconstrained) or `Mock(spec=["send_signal", "wait"])` (stricter, catches accidental calls to unexpected methods like `.poll()`) both work; prefer `spec=` to catch typos/attribute-name drift against the real `subprocess.Popen` API surface used by this function.
- **`notify` and `kill_active_child` are imported by name into `orchestrator.runtime`** (`from .notify import notify`, `from .agents import kill_active_child`), so monkeypatching must target `orchestrator.runtime.notify` / `orchestrator.runtime.kill_active_child` (the bound names in the `runtime` module namespace), not `orchestrator.notify.notify` / `orchestrator.agents.kill_active_child` — patching the origin module would not affect calls made from inside `runtime.py`.
