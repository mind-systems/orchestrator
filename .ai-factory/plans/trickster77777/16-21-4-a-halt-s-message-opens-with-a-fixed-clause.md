# Plan: 21.4 — A halt's message opens with a fixed clause

## Context

`main.py:515` cuts a `HaltError`'s message to its first line and hands that to `report(...)` as `HALTED`'s detail. Six of the eight halt sites open with a fixed summary clause; two do not — `RateLimitError(result_text)` (`agents.py:350`) is entirely the agent's own result text, and the named-roadmap owner mismatch (`main.py:152-155`) carries a `.ai-factory/roadmaps/` path and a quoted roadmap line inside its single line. Both reach the alert whole, which invariant 5 of `docs/concepts/fault-handling.md` forbids ("Its detail is a short fixed label or nothing, whatever produced the outcome"). This task reshapes exactly those two messages and states the convention on `HaltError` itself.

Assumption recorded from the spec (`.ai-factory/specs/trickster77777/56-a-halt-opens-with-a-fixed-clause.md`, "What NOT to do"): the touch-list is `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py` **only**. The convention the task line asks to "state" is therefore stated in code — on the `HaltError` base class every halt site raises or subclasses — not in `docs/concepts/fault-handling.md`, which already carries the invariant this convention serves and stays untouched.

## Settings
- Testing: yes (two cases, mandated by the spec)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Reshape the two offending messages

- [x] **Task 1: Give `RateLimitError` a fixed first line**
  Files: `orchestrator/agents.py`
  At the `verdict == "ratelimit"` branch (`agents.py:350`), replace `raise RateLimitError(result_text)` with a two-line message in the same shape the two `NetworkError` sites above it already use (`:340-347`): a fixed clause first, the variable text below.
  ```python
  raise RateLimitError(f"Agent reported a rate limit\n{result_text}")
  ```
  Keep the exception type exactly as declared — no new type, no new field, no truncation of `result_text` (the console at `main.py:513` prints the whole message and must keep showing the agent's text).

- [x] **Task 2: Give the named-roadmap owner mismatch a fixed first line**
  Files: `orchestrator/main.py`
  In `_resolve_roadmap_relpath` (`main.py:152-155`), reshape the `HaltError` so the fixed clause is the entire first line and `relpath` plus the two quoted identity strings move to a second line:
  ```python
  raise HaltError(
      f"Named roadmap owner line does not match the current git identity\n"
      f"{relpath}: {first_line!r} vs. expected {expected_owner!r}"
  )
  ```
  Nothing else in `_resolve_roadmap_relpath` changes — the `HaltError` at `:137` (no git identity), the missing-file fallback print at `:144`, and the return values stay byte-identical.

- [x] **Task 3: State the convention on `HaltError`** (depends on Task 1, Task 2)
  Files: `orchestrator/agents.py`
  Extend the `HaltError` docstring (`agents.py:150-151`) so the rule every future halt site must follow is stated once, at the type all eight sites raise or subclass: the message opens with a fixed clause naming what happened, and anything variable — a path, a quoted line, an agent's own text, captured output — goes on a later line, because the first line becomes the `HALTED` notification's whole detail while the console keeps printing the message in full.
  Keep it to behaviour: no phase/roadmap/plan references, no `.ai-factory/` paths in the docstring. Leave the `RateLimitError` and `NetworkError` docstrings as they are — the rule is inherited, not restated.

### Phase 2: Cover the two reshaped first lines

- [x] **Task 4: Drive the rate-limit halt and assert its first line** (depends on Task 1)
  Files: `tests/test_agents.py`
  Add one case near the `_classify_result` block (`tests/test_agents.py:541+`) that drives the real raise site rather than reconstructing the string. Pattern:
  - `monkeypatch.setattr(agents, "_CLAUDE_BIN", "/usr/local/bin/claude")` so `_resolve_claude()` is never called;
  - a minimal fake process class exposing `stdout` (an iterator over one JSON line, e.g. `{"session_id": "s1", "result": "You hit your limit, resets at 5pm"}`), `wait()`, and `returncode = 1` — mirroring the existing stand-in style at `tests/test_agents.py:511`;
  - `monkeypatch.setattr(agents.subprocess, "Popen", lambda *a, **kw: fake)`;
  - call `agents._run_claude("prompt", cwd=str(tmp_path))` inside `pytest.raises(RateLimitError)`.
  Assert `str(exc.value).splitlines()[0] == "Agent reported a rate limit"` and that the original result text appears on a later line (`"You hit your limit, resets at 5pm" in str(exc.value).split("\n", 1)[1]`). This verdict raises on the first attempt (`_classify_result` returns `"ratelimit"` regardless of attempt count — see `tests/test_agents.py:593`), so no retry sleep is entered. Import `RateLimitError` alongside the existing `HaltError`/`EscalationError` imports at the top of the file.
  The case must request the existing `clean_active_proc` fixture (`tests/test_agents.py:449`) alongside `monkeypatch` and `tmp_path` — unconditionally, the way the four neighbouring cases at `:466`, `:473`, `:489`, `:525` do. Do not hand-roll a reset and do not make it conditional on whether the case leaves the global set: this is the only case in the file that drives `_run_claude`, which assigns `state.active_proc` at `agents.py:277`, and the fixture is the file's established guard for that module-level global.

- [x] **Task 5: Drive the owner-mismatch halt and assert its first line** (depends on Task 2)
  Files: `tests/test_main.py`
  Add one case immediately after `test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt` (`tests/test_main.py:1139`), reusing `_config_with_roadmap_path` and `_fake_git_config` exactly as the neighbouring cases do. Build the same mismatched roadmap file, capture the exception with `with pytest.raises(HaltError) as exc:`, then assert:
  - `str(exc.value).splitlines()[0] == "Named roadmap owner line does not match the current git identity"` — the fixed clause alone, with no path and no quoted line in it;
  - the remainder contains `roadmaps/john-doe.md` and both quoted identities.
  Leave both existing cases that reach `main.py:152` untouched: `test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt` (`tests/test_main.py:1139`) and `test_resolve_roadmap_relpath_my_malformed_first_line_raises_halt` (`tests/test_main.py:1151`, whose `"# Not an owner line"` first line fails the same `first_line.strip() != expected_owner` guard). Both use a bare `pytest.raises(HaltError)` with no `match=`, so both keep passing unchanged.

### Phase 3: Verify

- [x] **Task 6: Confirm all eight halt sites and run the suite** (depends on Task 3, Task 4, Task 5)
  Files: `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/usage.py` (read-only), `orchestrator/notify.py` (read-only)
  Read the eight halt sites — `agents.py:340`, `:344`, the reshaped `:350`, `main.py:137`, the reshaped `:152`, `:321`, `usage.py:48`, `:52` — and confirm every first line is now a fixed clause, and that the six previously compliant messages are byte-identical to before. Confirm `compose()`, `report()`, `_WORDS`, `_ALERT_TYPES` in `notify.py` and the `except HaltError` arm at `main.py:511-517` are unchanged. Run `uv run pytest` from `orchestrator/` and confirm green, including the two new cases.
