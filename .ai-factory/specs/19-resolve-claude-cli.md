# Claude CLI Resolution — Test Plan

**Date:** 2026-07-13
**Source:** roadmap-test-coverage agent

## Source Overview

`_resolve_claude()` (`orchestrator/agents.py:81-95`) locates the `claude` CLI binary: it first tries `shutil.which("claude")` (PATH lookup), and if that fails, falls back to scanning `~/.nvm/versions/node/<version>/bin/claude` for nvm-managed Node installs, picking the first directory that has a `claude` binary when the version directories are sorted in reverse. Its result is cached once in the module-level global `_CLAUDE_BIN` (`agents.py:98`) and consumed by `_run_claude()` (`agents.py:111-113`), which only calls `_resolve_claude()` when `_CLAUDE_BIN is None`. This runs once per process at the start of every agent invocation (planner, reviewer, implementer) — get it wrong and every downstream Claude CLI call either fails to start or silently launches the wrong installed binary.

## Instantiation

- Call `_resolve_claude()` directly (from `orchestrator.agents`); it takes no arguments and has no required object state, so no fixture/constructor is needed beyond monkeypatching its two OS-touching dependencies.
- **`shutil.which`**: monkeypatch `agents.shutil.which` directly (not a top-level `shutil.which` patch), since `agents.py` does `import shutil` — to return a controlled value (a path string or `None`).
- **`Path.home()`**: monkeypatch `agents.Path.home` (same object as `pathlib.Path` since `agents.py` does `from pathlib import Path`) via `monkeypatch.setattr(agents.Path, "home", lambda: tmp_path / "fakehome")` to point at a fake home directory built under pytest's `tmp_path`.
- **Fake nvm tree**: under the fake home, build `.nvm/versions/node/<version-dir>/bin/claude` as needed per test, using `tmp_path`-relative `Path.mkdir(parents=True)` and `Path.write_text("")` (or just `touch`) to create the `claude` file. The code only checks `candidate.exists()` — content doesn't matter, an empty file suffices.
- **Gotcha — module global caching**: `_CLAUDE_BIN` is set once at module scope and reused across calls to `_run_claude`. Tests that exercise `_resolve_claude()` directly are unaffected (it never reads or writes `_CLAUDE_BIN`). But any test that goes through `_run_claude()` must reset `agents._CLAUDE_BIN` to `None` before the test (e.g. `monkeypatch.setattr(agents, "_CLAUDE_BIN", None)`) — otherwise a value cached by an earlier test in the same process will silently short-circuit `_resolve_claude()` and the test will pass/fail for the wrong reason. Recommend testing `_resolve_claude()` directly and unit-testing the cache/call-site behavior in `_run_claude` separately (a single focused test verifying `_resolve_claude` is not called a second time once `_CLAUDE_BIN` is set, via a call-count spy).

## Existing Coverage

None. `grep -n "_resolve_claude\|_CLAUDE_BIN" tests/test_agents.py tests/test_main.py` returns no matches. No test file currently exists for this behavior.

## Test Cases

### PATH lookup (primary path)

- **should return the PATH-resolved path directly when `shutil.which("claude")` finds it**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `agents.shutil.which` to return a fixed string, e.g. `"/usr/local/bin/claude"`. Assert `_resolve_claude()` returns exactly that string.
- **should never consult the nvm fallback when `shutil.which` succeeds**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `agents.shutil.which` to return a path; additionally monkeypatch `Path.home` to point at a directory that does NOT exist (or has no `.nvm`), or spy on `Path.home`/`Path.is_dir` to assert it's never invoked. Confirms short-circuit: no `~/.nvm` access is attempted once PATH lookup succeeds.

### Nvm fallback — not found

- **should raise FileNotFoundError with install-instruction message when `shutil.which` returns None and `~/.nvm` doesn't exist at all**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home` → a `tmp_path` subdir that is never created (or created but with no `.nvm` inside). Assert `pytest.raises(FileNotFoundError, match="npm install -g @anthropic-ai/claude-code")`.
- **should raise FileNotFoundError when `~/.nvm/versions/node/` exists but is empty**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create `<fakehome>/.nvm/versions/node/` as an empty directory. Assert `FileNotFoundError` raised with the same install message.

### Nvm fallback — found, multiple candidates

- **should return the claude binary from the highest-sorting version directory when multiple nvm version dirs each have `bin/claude`**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create `<fakehome>/.nvm/versions/node/v18.0.0/bin/claude` and `.../v20.1.0/bin/claude` (both real files under `bin/`). Assert the returned path is the `v20.1.0` one — this is the case where lexicographic sort happens to agree with semver order, so it's a legitimate "happy path" sanity check, not proof the sort logic is correct in general (see Gotchas).
- **should silently return the WRONG (lexicographically-highest, not semver-highest) binary when version numbers cross a digit-width boundary — e.g. "v9.0.0" vs "v10.0.0"**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create `<fakehome>/.nvm/versions/node/v9.0.0/bin/claude` and `.../v10.0.0/bin/claude`. Assert the function returns the `v9.0.0` binary (documenting the actual, buggy behavior) — this test exists to pin down and make visible the latent bug (see Gotchas), not to bless it as correct. If/when the code is fixed to do a true semver-aware sort, this test's expected value should flip to `v10.0.0` and the test renamed accordingly.

### Nvm fallback — partial installs

- **should skip nvm version dirs that lack a `bin/claude` file and fall through to the next candidate**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create `<fakehome>/.nvm/versions/node/v20.1.0/` with no `bin/` subdirectory at all (or a `bin/` dir missing the `claude` file), and `<fakehome>/.nvm/versions/node/v18.0.0/bin/claude` present. Assert the function returns the `v18.0.0` path, not a nonexistent `v20.1.0` path, and does not raise.
- **should raise FileNotFoundError when nvm version dirs exist but none has a `bin/claude` file**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create two or more version dirs (`v18.0.0`, `v20.1.0`) each without a working `bin/claude` (either no `bin/` dir, or `bin/` present but no `claude` file inside). Assert `FileNotFoundError` raised with the install-instruction message.
- **should skip a non-version, unrelated entry in the nvm node directory without crashing (e.g. a stray file or `.DS_Store`-like entry)**
  Exercises: `_resolve_claude`
  Setup: monkeypatch `shutil.which` → `None`; monkeypatch `Path.home`; create `<fakehome>/.nvm/versions/node/somefile` as a plain file (not a directory) alongside a valid `v18.0.0/bin/claude`. Assert no crash (the code does `node_dir / "bin" / "claude"` and calls `.exists()` — this works fine even if `node_dir` is a file, since `.exists()` on a bogus nested path just returns `False`) and the valid candidate is still returned. This guards against an implicit assumption that every entry in `nvm_base.iterdir()` is a directory.

### Cache / call-site behavior (via `_run_claude`)

- **should call `_resolve_claude` only once across multiple `_run_claude` invocations when `_CLAUDE_BIN` is already cached**
  Exercises: `_run_claude`'s use of `_CLAUDE_BIN` (agents.py:111-113)
  Setup: monkeypatch `agents._resolve_claude` with a call-counting stub returning a fixed path; monkeypatch `agents._CLAUDE_BIN` to `None` initially (via `monkeypatch.setattr`, so it's restored after the test); monkeypatch `subprocess.Popen` (or the rest of `_run_claude`'s internals) to avoid actually spawning a process. Call `_run_claude` twice; assert the stub was invoked exactly once and `agents._CLAUDE_BIN` holds the resolved value after the first call.
- **should re-raise the FileNotFoundError from `_resolve_claude` when `_run_claude` is invoked and no CLI can be found**
  Exercises: `_run_claude` → `_resolve_claude` call site
  Setup: monkeypatch `agents._CLAUDE_BIN` to `None`; monkeypatch `agents.shutil.which` → `None` and `Path.home` to a fake home with no `.nvm`. Call `_run_claude(...)` and assert `FileNotFoundError` propagates before any subprocess is spawned (i.e., `subprocess.Popen` is never called — can assert via a monkeypatched Popen that raises/records if invoked).

## Refactor Required

Testability review verdict: `_resolve_claude` calls `shutil.which`/`Path.home()` directly instead of taking them as injectable params, and the module-level `_CLAUDE_BIN` cache (mutated via `global`) is a hidden singleton that tests must manually monkeypatch/reset for isolation.

Possible post-refactor shape: `_resolve_claude(which=shutil.which, home=Path.home)` with the current calls as defaults — callers unaffected, tests pass fakes directly instead of monkeypatching `agents.shutil`/`agents.Path`. The `_CLAUDE_BIN` cache is lower-priority: it's a legitimate memoization (resolve once per process), and the test plan above already shows a working reset pattern (`monkeypatch.setattr(agents, "_CLAUDE_BIN", None)`) — not a hard blocker for testing, just a bit of required boilerplate per test. The nvm lexicographic-vs-semver sort bug documented below is the more consequential finding from this research; the DI refactor is optional polish for the decomposition stage to weigh, not required to write the tests in this note.

## Gotchas

- **Lexicographic sort, not semver sort — real latent bug.** `sorted(nvm_base.iterdir(), reverse=True)` sorts `Path` objects, which compare by their string form. Nvm version directory names look like `v18.20.4`. String comparison is lexicographic, so any pair of versions whose major (or minor/patch) version numbers differ in digit count can sort backwards from true semver order — verified empirically: `sorted(["v9.0.0","v10.0.0","v18.20.4","v20.11.0"], reverse=True)` yields `['v9.0.0', 'v20.11.0', 'v18.20.4', 'v10.0.0']`, i.e. `v9.0.0` (an old install) is picked over `v20.11.0`, `v18.20.4`, and `v10.0.0` — the actual latest version. In practice this only bites once a user has both a single-digit and a double-digit major (or minor) Node version installed via nvm on the same machine (e.g. upgrading past v9→v10, or v9.x.x→v10.x.x minor bumps), which is plausible over the life of a long-lived dev machine. This fails silently: no crash, no warning — `_resolve_claude` just returns a path to a stale claude binary, and every subsequent `_run_claude` call silently uses the wrong CLI version. Flagging as a real bug worth a follow-up fix (e.g. `packaging.version.parse` or a numeric-tuple sort key), not just a test-case footnote.
- **`_CLAUDE_BIN` global cache causes test-order coupling.** Any test that exercises `_run_claude` (or imports `agents` and happens to trigger it) can poison `agents._CLAUDE_BIN` for the rest of the test session unless explicitly reset via `monkeypatch.setattr(agents, "_CLAUDE_BIN", None)`. Prefer testing `_resolve_claude()` directly wherever possible to sidestep this entirely.
- **Patch target matters.** Because `agents.py` does `import shutil` (not `from shutil import which`), tests must patch `agents.shutil.which`, not a top-level `shutil.which` — patching the wrong reference silently no-ops and the real system `shutil.which("claude")` runs, which is both flaky (depends on the test machine's actual PATH) and could mask bugs in CI vs. locally.
- **`Path.home()` patch scope.** `Path.home` is a classmethod on `pathlib.Path`; patching it via `monkeypatch.setattr(agents.Path, "home", ...)` affects any other code path in the same test that calls `Path.home()` — keep test scope tight and rely on `monkeypatch`'s automatic teardown rather than manual restoration.
- **`Path.is_dir()` / `.exists()` on the fake tree must be real filesystem operations under `tmp_path`** (not further mocked) — this keeps the test faithful to actual iteration/sort/exists behavior rather than mocking away the exact logic under test.
- **No test needed for "malformed nvm path that raises `PermissionError`/`OSError`"** per test philosophy — that's a loud failure (unhandled exception propagates), not a silent wrong-answer surface, so it's out of scope for this plan unless the code changes to swallow such errors.
