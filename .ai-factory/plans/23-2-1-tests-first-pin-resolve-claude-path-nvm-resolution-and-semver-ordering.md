# Plan: 2.1 — Tests-first: pin `_resolve_claude` PATH/nvm resolution and semver ordering

## Context
Add the first test coverage for `_resolve_claude` (`orchestrator/agents.py:81`): PATH-hit, all not-found paths, partial-install skipping, and non-dir tolerance land green against current code, while a semver-ordering assertion (`v9.0.0` vs `v20.11.0` must pick `v20.11.0`) is pinned RED as the failing test that milestone 2.2's fix will turn green.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Test scaffolding

- [x] **Task 1: Extend `test_agents.py` imports and add a fake-nvm helper**
  Files: `tests/test_agents.py`
  Add `from orchestrator import agents` to the existing imports (keep the current `from orchestrator.agents import _has_signal, TestRunner`). Add a small module-level helper `_make_claude_bin(node_dir: Path) -> Path` that creates `node_dir / "bin" / "claude"` via `mkdir(parents=True)` + `write_text("")` and returns the created binary path (content is irrelevant — `_resolve_claude` only calls `.exists()`). Add a comment-delimited section header block matching the file's existing style (e.g. `# --- _resolve_claude ---`). Do not touch the existing `_has_signal` / `TestRunner` tests.
  Per the spec (`.ai-factory/specs/19-resolve-claude-cli.md` § Instantiation): monkeypatch `agents.shutil.which` and `agents.Path.home` (never a top-level `shutil.which`), build fake trees under pytest's `tmp_path`, and keep `.exists()`/`.is_dir()` as real filesystem ops on `tmp_path` (do not mock them).

### Phase 2: Green cases — current behavior

- [x] **Task 2: PATH-hit tests** (depends on Task 1)
  Files: `tests/test_agents.py`
  Two tests exercising the `shutil.which` primary path:
  - `shutil.which("claude")` returns a fixed string (e.g. `"/usr/local/bin/claude"`) → `agents._resolve_claude()` returns exactly that string.
  - PATH hit short-circuits the nvm fallback: `agents.shutil.which` returns a path AND `agents.Path.home` is patched to a non-existent `tmp_path` subdir (no `.nvm`); assert the returned value is the PATH string and no `FileNotFoundError` is raised (the nvm branch is never reached).
  Monkeypatch `agents.shutil.which` and `agents.Path.home` per Task 1's helper conventions.

- [x] **Task 3: Not-found tests → `FileNotFoundError` with install message** (depends on Task 1)
  Files: `tests/test_agents.py`
  Three tests, each with `agents.shutil.which` → `None` and `agents.Path.home` → a `tmp_path` fake home, asserting `pytest.raises(FileNotFoundError, match="npm install -g @anthropic-ai/claude-code")`:
  - `~/.nvm` does not exist at all (fake home created but no `.nvm` inside).
  - `<fakehome>/.nvm/versions/node/` exists but is empty.
  - Version dirs exist (`v18.0.0`, `v20.1.0`) but none has a `bin/claude` file.

### Phase 3: Green cases — nvm candidate selection

- [x] **Task 4: Multi-candidate, partial-install, and non-dir tolerance tests** (depends on Task 1)
  DEVIATION: plan said "Four tests" but only three cases were listed below it / implemented the three listed cases (multi-candidate, partial-install, non-dir tolerance) / done.
  Files: `tests/test_agents.py`
  Four tests, all with `agents.shutil.which` → `None` and `agents.Path.home` → a `tmp_path` fake home; assert the returned path equals the expected `str(candidate)`:
  - Happy multi-candidate (sort agrees with semver): `v18.0.0/bin/claude` and `v20.1.0/bin/claude` both present → returns the `v20.1.0` binary.
  - Partial install skipped: `v20.1.0/` present with no `bin/claude`, `v18.0.0/bin/claude` present → returns the `v18.0.0` binary, no raise.
  - Non-dir entry tolerated: a plain file `<fakehome>/.nvm/versions/node/somefile` alongside a valid `v18.0.0/bin/claude` → returns the `v18.0.0` binary, no crash.
  Use the `_make_claude_bin` helper from Task 1 to build each `bin/claude`.

### Phase 4: RED case — semver ordering

- [x] **Task 5: Ordering assertion pinned RED until 2.2** (depends on Task 1)
  Files: `tests/test_agents.py`
  One test: `agents.shutil.which` → `None`; fake home with both `<fakehome>/.nvm/versions/node/v9.0.0/bin/claude` and `.../v20.11.0/bin/claude` present. Assert the resolver returns the **`v20.11.0`** binary (the true-latest / correct semver pick) — this is RED against today's `sorted(..., reverse=True)` lexicographic sort, which picks `v9.0.0`.
  Mark it `@pytest.mark.xfail(reason="lexicographic sort picks v9.0.0 over v20.11.0 — fixed in 2.2", strict=True)` so the suite as a whole stays green now (the assertion is expected-to-fail), and `strict=True` forces the expected XPASS→failure once 2.2's semver fix lands, requiring 2.2 to remove the marker. The assertion itself encodes the correct behavior per the milestone contract (which overrides spec note 19's case #47 that documents the buggy `v9.0.0` pick).

## Commit Plan
- **Commit 1** (after tasks 1-3): "Add _resolve_claude PATH-hit and not-found tests"
- **Commit 2** (after tasks 4-5): "Cover nvm candidate selection and pin semver ordering red"
