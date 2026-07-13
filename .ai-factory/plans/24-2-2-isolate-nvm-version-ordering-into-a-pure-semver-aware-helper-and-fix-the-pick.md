# Plan: 2.2 — Isolate nvm version ordering into a pure semver-aware helper and fix the pick

## Context
Replace the lexicographic `sorted(..., reverse=True)` pick in `_resolve_claude` with a pure, semver-aware `_sorted_nvm_node_dirs` helper so the resolver launches the true-latest nvm claude binary (`v20.11.0` over `v9.0.0`), turning the RED ordering test from 2.1 green.

## Settings
- Testing: yes (flip the RED case green + add the spec-mandated direct helper unit cases)
- Logging: minimal
- Docs: no

## Assumptions / deviation note
- The milestone text says "touch `agents.py` only", but its own verify requires `uv run pytest` green. Ground truth in `tests/test_agents.py` shows the ordering case `test_resolve_claude_semver_ordering_picks_true_latest` carries `@pytest.mark.xfail(reason=..., strict=True)`. Once the fix lands, that test XPASSes, and under `strict=True` an unexpected pass is reported as a **suite failure** — so the suite cannot go green without also removing that xfail marker. Task 2 makes the mandatory edits to the test file. This is the standard TDD RED→green flip; the "agents.py only" phrasing did not account for how 2.1 encoded RED.
- `specs/20-resolve-claude-semver-fix.md:30` calls for direct unit cases on the pure helper (single- vs double-digit majors, unparseable-sorts-last, empty list). The spec attributes them to 2.1, but 2.1 was authored RED before this helper existed and the current `tests/test_agents.py` contains no helper-level test — so no task owns them. Since these are exactly the never-raise / total-ordering silent-failure surfaces this milestone exists to guarantee, Task 2 adds them (the file is already being edited). This consciously fulfills the governing spec rather than skipping it.

## Tasks

### Phase 1: Pure ordering helper + rewired pick

- [x] **Task 1: Add `_sorted_nvm_node_dirs` and rewire `_resolve_claude`**
  Files: `orchestrator/agents.py`
  Add a module-level pure function `_sorted_nvm_node_dirs(dirs: list[Path]) -> list[Path]` directly above `_resolve_claude` (currently `agents.py:81`). No filesystem access — it only inspects `Path.name`.
  - For each dir, strip a leading `v` from `name`, split on `.`, and take the leading run of all-decimal segments into an int tuple (e.g. `v18.20.4` → `(18, 20, 4)`, `v20.11.0` → `(20, 11, 0)`).
  - Use `str.isdecimal()` (NOT `str.isdigit()`) as the per-segment integer guard: `str.isdigit()` returns `True` for Unicode numeric forms (e.g. superscript `"²"`) that `int()` rejects with `ValueError`, which would break the never-raise contract; `str.isdecimal()` is exactly the set `int()` accepts for ASCII/decimal digits. (Equivalently, wrap `int()` in try/except — but `isdecimal()` is the intended shape.)
  - Sort key must make parseable versions (at least one leading decimal segment) always outrank unparseable names, highest version first; unparseable names (no leading decimal segment — e.g. `system`, `lts`, a stray file like `zzstray`) sort **last**, ordered among themselves by their string `name`. Use a composite key such as `(1, version_tuple)` for parseable vs `(0,)`-tier for unparseable with `reverse=True`, or an equivalent total-ordering key — the contract is the ordering, never raising, and being deterministic. Avoid comparing an int-tuple against a string across types by keeping the leading tier discriminator distinct.
  - The function must never raise on any input, including an empty list (returns `[]`) and names with mixed/trailing non-integer segments.
  - Then rewrite the nvm-fallback loop in `_resolve_claude`: replace `for node_dir in sorted(nvm_base.iterdir(), reverse=True):` with `for node_dir in _sorted_nvm_node_dirs(list(nvm_base.iterdir())):`, keeping the `candidate = node_dir / "bin" / "claude"` / `if candidate.exists(): return str(candidate)` body byte-identical.
  - Leave everything else untouched: the `shutil.which` PATH-hit branch and its early return, the `nvm_base.is_dir()` guard, the `FileNotFoundError` install-instruction message, and the `_CLAUDE_BIN` module cache. No new imports (all needed pieces are already available).

### Phase 2: Flip the RED test green, correct stale reasoning, add helper unit cases

- [x] **Task 2: Update `tests/test_agents.py` — unblock, de-stale, and cover the helper** (depends on Task 1)
  Files: `tests/test_agents.py`
  Three edits, all within this one already-edited file:
  1. **Remove the strict xfail marker.** Delete the `@pytest.mark.xfail(reason="lexicographic sort picks v9.0.0 over v20.11.0 — fixed in 2.2", strict=True)` decorator on `test_resolve_claude_semver_ordering_picks_true_latest` (currently `tests/test_agents.py:259-262`) so the now-passing assertion is a normal green test. Leave the test body/name unchanged.
  2. **Fix the now-false reasoning in `test_resolve_claude_non_dir_entry_tolerated`** (`tests/test_agents.py:240-251`). After the fix an unparseable name sorts **last**, not ahead of a version dir. Update the docstring (drop the "sorting ahead of the valid version dir under reverse=True is visited first" claim → state the stray non-dir entry is tolerated and skipped, and the valid `v18.0.0` candidate is still returned) and the inline comment at line 247 (`# sorts before v18.0.0 under reverse=True` → note it is a stray non-version entry that sorts last / is skipped). Assertion stays as-is — v18 is still returned.
  3. **Add direct unit cases for `_sorted_nvm_node_dirs`** (spec `20-...md:30`). Add a small test block calling `agents._sorted_nvm_node_dirs` on plain `Path` lists — no monkeypatching, no tmp tree needed (build `Path("v9.0.0")`-style paths in memory and compare `.name` on the returned order). Cover:
     - Single- vs double-digit majors order semantically: input `[Path("v9.0.0"), Path("v20.11.0"), Path("v10.0.0")]` → returns `v20.11.0`, `v10.0.0`, `v9.0.0` (highest-first, the exact bug this milestone fixes).
     - Unparseable-sorts-last: a mix like `[Path("v18.20.4"), Path("system"), Path("v20.1.0")]` → both `v` versions precede `system`, and among two unparseable names they order by string.
     - Empty list → `[]`, never raises.
  Then run `uv run pytest` to confirm the whole suite (the previously-RED ordering assertion, all 2.1 `_resolve_claude` cases, and the new helper cases) is green.
