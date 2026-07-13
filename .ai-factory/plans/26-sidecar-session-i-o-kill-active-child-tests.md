# Test Plan: Sidecar session I/O + `kill_active_child` tests

## Context
`_read_sessions`, `_write_session`, and `kill_active_child` (`orchestrator/agents.py:47,57,19`) are the persistence backbone for resuming an interrupted pipeline run and for safely tearing down the in-flight Claude CLI child on Ctrl-C. They currently have no direct tests, yet both swallow errors silently — corrupt sidecar JSON degrades to `{}` on read and, worse, `_write_session` drops all prior keys (losing a session ID) on corruption. These tests characterize the real behavior, including the data-loss surface, so a future reader knows it is observed, not necessarily desired.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/ -v`

## Target Spec File
`tests/test_agents.py`

## Tasks

### Phase 1: `_read_sessions` — reading the sidecar

- [x] **Task 1: `_read_sessions` reads and degrades the sidecar**
  Files: `tests/test_agents.py`
  Import: `from orchestrator.agents import _read_sessions`. Build `plan_path = tmp_path / "01-foo-plan.md"` (the `.md` file itself need not exist); the sidecar is `tmp_path / "01-foo-plan.json"`.
  Test cases:
  - `should return {} when the sidecar file does not exist` — do not create the `.json`; assert `_read_sessions(plan_path) == {}`.
  - `should return the parsed dict when the sidecar contains valid JSON` — write `{"planner": "sid-123", "step": "planned"}` to the sidecar; assert the returned dict equals it exactly (keys and values round-trip).
  - `should return {} silently when the sidecar contains malformed JSON` — write raw garbage (e.g. `"{not valid json"`) to the sidecar; assert the result is `{}` and no exception is raised (covers the `except (json.JSONDecodeError, OSError)` swallow).
  - `should derive the sidecar path via .with_suffix('.json') not by appending` — use `plan_path = tmp_path / "03-bar-plan.md"`, write the sidecar to `tmp_path / "03-bar-plan.json"` (not `03-bar-plan.md.json`); assert `_read_sessions` finds and returns its contents, proving suffix replacement rather than append.

### Phase 2: `_write_session` — writing and merging the sidecar

- [x] **Task 2: `_write_session` create, merge, and overwrite**
  Files: `tests/test_agents.py`
  Import: `from orchestrator.agents import _write_session`. Read the resulting sidecar with `json.loads((tmp_path / "01-foo-plan.json").read_text())`.
  Test cases:
  - `should create a fresh sidecar containing only the new key when none exists yet` — fresh `tmp_path`, no pre-existing `.json`; call `_write_session(plan_path, "planner", "sid-abc")`; assert the sidecar exists and its parsed content equals `{"planner": "sid-abc"}`.
  - `should merge the new key into an existing sidecar without clobbering other keys` — pre-seed the sidecar with `{"planner": "sid-abc", "step": "planned"}`; call `_write_session(plan_path, "implementer", "sid-xyz")`; assert content equals `{"planner": "sid-abc", "step": "planned", "implementer": "sid-xyz"}`.
  - `should overwrite the value of an existing key when writing the same key again` — pre-seed `{"planner": "sid-old"}`; call `_write_session(plan_path, "planner", "sid-new")`; assert content equals `{"planner": "sid-new"}`.

- [x] **Task 3: `_write_session` corruption fallback and atomic write**
  Files: `tests/test_agents.py`
  Test cases:
  - `should fall back to a fresh dict dropping prior data when the existing sidecar is corrupted JSON` — write garbage text to the sidecar first, then call `_write_session(plan_path, "step", "planned")`; assert the sidecar now contains **only** `{"step": "planned"}` (no recovery of prior data, no merge, no raise). This is the data-loss silent-failure surface — name/docstring it as observed behavior.
  - `should leave no .tmp file behind after a successful write` — fresh `tmp_path`; call `_write_session`; assert `plan_path.with_suffix('.json.tmp')` does **not** exist afterward while the final `.json` does (verifies the `tmp.write_text(...); os.replace(tmp, p)` pattern completed and did not leak the intermediate file).
  - `should produce sidecar content that is re-readable via _read_sessions` — call `_write_session` twice with different keys, then call `_read_sessions` on the same `plan_path`; assert both keys are present (round-trip check that the two functions agree on path derivation and format).

### Phase 3: `kill_active_child` — teardown of the active child

- [x] **Task 4: `kill_active_child` no-op branches**
  Files: `tests/test_agents.py`
  Import: `from orchestrator import state; from orchestrator.agents import kill_active_child`. `state.active_proc` is a shared module-level global — save its prior value and reset to `None` in a `try/finally` (or a fixture) around every case so leftover state cannot corrupt other tests.
  Test cases:
  - `should be a no-op and leave state.active_proc as None when it is already None` — explicitly set `state.active_proc = None`; call `kill_active_child()`; assert no exception and `state.active_proc is None`.
  - `should clear state.active_proc without signalling when the tracked process has already exited` — spawn a trivial real process (`subprocess.Popen(["true"])` or `["sleep", "0"]`), call `.wait()` so `poll()` returns a non-`None` exit code, assign it to `state.active_proc`, then call `kill_active_child()`; assert `state.active_proc is None` and no exception (covers the `proc.poll() is not None` short-circuit — `os.killpg` is not reached).

- [x] **Task 5: `kill_active_child` kills a live process group**
  Files: `tests/test_agents.py`
  Same `state.active_proc` save/reset discipline in `try/finally`.
  Test cases:
  - `should kill the live process group and clear state.active_proc when the process is still running` — `proc = subprocess.Popen(["sleep", "5"], preexec_fn=os.setsid)` (own process group, matching `_run_claude`'s `start_new_session=True`); set `state.active_proc = proc`; call `kill_active_child()`; poll in a short retry loop (SIGKILL delivery is not synchronous — e.g. up to ~1s) until `proc.poll() is not None`; assert the process died (non-`None`, killed-by-signal returncode) and `state.active_proc is None`. Call `proc.wait()` in cleanup to reap the child.

- [x] **Task 6: `kill_active_child` killpg-failure fallback**
  Files: `tests/test_agents.py`
  Test cases:
  - `should fall back to proc.kill() and still clear state.active_proc when os.killpg raises ProcessLookupError` — this except branch is impractical to trigger with a real race, so use a lightweight fake: an object exposing `.poll()` returning `None`, a `.pid` attribute, and a mock `.kill()`; monkeypatch `agents.os.killpg` to raise `ProcessLookupError`; set `state.active_proc` to the fake; call `kill_active_child()`; assert the fake's `.kill()` was called and `state.active_proc is None` afterward.
