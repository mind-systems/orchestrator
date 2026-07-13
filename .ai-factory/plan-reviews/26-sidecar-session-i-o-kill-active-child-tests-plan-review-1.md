## Plan Review Summary

**Plan:** Test Plan: Sidecar session I/O + `kill_active_child` tests
**Files Reviewed:** plan + `orchestrator/agents.py`, `orchestrator/state.py`, `tests/test_agents.py`, `tests/conftest.py`, spec `.ai-factory/specs/19-sidecar-session-io.md`, `ROADMAP_TESTS.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap linkage** — ✅ The plan implements the `ROADMAP_TESTS.md:15` line **"Sidecar session I/O + `kill_active_child` tests"** (`tests/test_agents.py`, `Spec: .ai-factory/specs/19-sidecar-session-io.md`). Every case enumerated on that contract line is present: missing→`{}`, valid round-trip, malformed→`{}`, `.with_suffix('.json')` derivation, fresh-create, merge, same-key overwrite, corruption-drops-prior, atomic no-`.tmp`, `None`/already-exited no-ops, live-kill, `killpg`→`ProcessLookupError` fallback, save/reset discipline. No milestone linkage is missing.
- **Spec conformance** — ✅ The plan is a faithful narrowing of `specs/19-sidecar-session-io.md`. It correctly declines the spec's optional DI refactor (the spec itself flags it as "a deviation from the established pattern, not a fix to a defect," and `ARCHITECTURE.md` sanctions the `state.py` global-flag pattern). Testing the global directly via save/reset is the right call.
- **Test philosophy** — ✅ Every targeted surface is silent-failure (swallowed `JSONDecodeError`/`OSError`, data-loss-on-corruption, session-clearing) — exactly the kind that fails quietly with wrong output. Appropriate to characterize.

### Verified Against Ground Truth
- **Line references** — `agents.py:19` = `kill_active_child`, `:47` = `_read_sessions`, `:57` = `_write_session`. Accurate.
- **Path derivation** — `_read_sessions`/`_write_session` use `plan_path.with_suffix('.json')`; the tmp file is `p.with_suffix('.json.tmp')`. Confirmed on Python 3.13 that both `plan_path.with_suffix('.json.tmp')` (from `.md`) and the code's `p.with_suffix('.json.tmp')` (from `.json`) resolve to the identical `01-foo-plan.json.tmp`, so Task 3's atomic-write assertion targets the correct file.
- **Corruption fallback (Task 3, case 1)** — Source confirms `except (json.JSONDecodeError, OSError): data = {}` then `data[key] = value`, so only the new key survives. The plan's "assert content is **only** `{"step": "planned"}`" is exactly right, and flagging it as observed-not-desired matches the spec's data-loss note.
- **`kill_active_child` branches** — `proc is None or proc.poll() is not None` → clears and returns (Task 4 both cases); live path `os.killpg(os.getpgid(proc.pid), SIGKILL)` matched by `Popen(["sleep","5"], preexec_fn=os.setsid)` giving pid==pgid (Task 5); `except (ProcessLookupError, PermissionError)` → `proc.kill()` matched by monkeypatching `agents.os.killpg` to raise `ProcessLookupError` (Task 6). All branch mappings are correct.
- **Imports** — `from orchestrator.agents import _read_sessions/_write_session/kill_active_child` and `from orchestrator import state` all resolve against the current module layout.
- **No collision** — new test names don't clash with the existing `_has_signal`/`_extract_test_command`/`_resolve_claude` suites in the same file; the conftest `NO_TESTS_COLLECTED` shim is irrelevant once these collect.

### Critical Issues
None.

### Positive Notes
- The save/reset-in-`try/finally` discipline for the shared `state.active_proc` global is called out on every `kill_active_child` task — the one real cross-test hazard, correctly neutralized.
- Task 6 sensibly uses a lightweight fake for the un-raceable `ProcessLookupError` branch instead of forcing a brittle real race; the fake reaches the fallback regardless of the `.pid` value, so the assertion holds either way.
- Task 3's round-trip case (`_write_session` ×2 → `_read_sessions`) pins that both functions agree on path derivation and format — cheap and load-bearing for the resume machinery.

PLAN_REVIEW_PASS
