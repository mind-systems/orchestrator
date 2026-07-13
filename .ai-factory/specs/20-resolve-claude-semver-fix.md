# Claude CLI nvm version pick — semver-aware ordering

**Date:** 2026-07-13
**Source:** conversation context

## Problem today

`_resolve_claude` (`agents.py:81`) falls back, when `shutil.which("claude")` misses, to scanning `~/.nvm/versions/node/` and picking the first version directory that has a `bin/claude`, using `sorted(nvm_base.iterdir(), reverse=True)`. `Path` objects sort by their string form, so this is a **lexicographic** sort, not a semantic-version sort. Confirmed empirically: `sorted(["v9.0.0","v10.0.0","v18.20.4","v20.11.0"], reverse=True)` yields `['v9.0.0', 'v20.11.0', 'v18.20.4', 'v10.0.0']` — `v9.0.0` (an old install) is chosen over the true latest `v20.11.0`. On any long-lived machine that has both a single-digit and a double-digit Node major installed via nvm, the tool silently launches an **older** claude binary: no crash, no warning, wrong engine. Since every agent run shells out through this resolver, a wrong pick degrades every planner/reviewer/implementer call.

## The fix — isolate ordering into a pure helper

Extract the version-directory ordering out of `_resolve_claude` into a pure function with no filesystem access:

- `_sorted_nvm_node_dirs(dirs: list[Path]) -> list[Path]` — returns the input in **best-first** order (highest version first).
- Ordering key: parse each dir name of the form `v<major>.<minor>.<patch>[...]` by stripping a leading `v` and splitting on `.`, taking the leading run of all-integer segments into an int tuple (e.g. `v18.20.4` → `(18, 20, 4)`). Sort by that tuple descending.
- **Unparseable names sort last** (after every parseable version), ordered among themselves by their string form — deterministic, never raises. A name with no integer segments (e.g. `system`, `lts`) falls into this bucket.
- Implementation shape: a sort key like `(0, ...)` for unparseable vs `(1, version_tuple)` for parseable so parseable always outranks, then `reverse=True`; or an equivalent `key=` returning a sortable composite. The contract is the ordering, not the mechanism.

`_resolve_claude` then iterates `_sorted_nvm_node_dirs(list(nvm_base.iterdir()))`, checking `node_dir / "bin" / "claude"` existence exactly as today, and returns the first hit. The PATH-lookup branch, the `_CLAUDE_BIN` cache, and the `FileNotFoundError` message are all unchanged.

## Guards / edge cases

- Never crash on a malformed directory name — the fallback key absorbs anything non-conforming.
- A non-directory entry in `~/.nvm/versions/node/` (a stray file) is tolerated: it flows through the helper (ordered by the fallback key) and the subsequent `.exists()` check on its bogus `bin/claude` sub-path simply returns `False`, so it is skipped — same as today.
- Do **not** add a third-party dependency (no `packaging`); a hand-rolled int-tuple key is sufficient and keeps zero deps (the project has `dependencies = []`).
- Pre-release / build-metadata suffixes are effectively absent in nvm node dir names; the leading-integer-run parse handles `v18.20.4` cleanly and any oddity lands in the unparseable bucket rather than mis-sorting.

## Tests

The test cases live in the tests-first task's plan (`.ai-factory/specs/19-resolve-claude-cli.md`) and are authored RED in task 2.1 against `tests/test_agents.py`. This task turns the **ordering** case green: with `v9.0.0` and `v20.11.0` both present, the resolver returns `v20.11.0`. The pure `_sorted_nvm_node_dirs` also gets direct unit cases (single- vs double-digit majors, unparseable-sorts-last, empty list) — no monkeypatching needed since it takes plain `Path`s.

## Verify

- `uv run pytest` green, including the previously-RED semver ordering assertion from 2.1.
- PATH-hit behavior, the not-found `FileNotFoundError` message, and `_CLAUDE_BIN` caching are byte-identical to before.

## What NOT to do

- Do not add a dependency or import `packaging`.
- Do not touch `_CLAUDE_BIN` caching or `_run_claude`.
- Do not change the `FileNotFoundError` install-instruction message.
- Do not change the PATH-lookup-first ordering (`shutil.which` still wins before any nvm scan).
