# Plan: `_artifact_subdir`: strip the `-tests` suffix — one stem keys the whole roadmap pair

## Context
Make a named roadmap pair share one artifact-subdirectory stem (`roadmaps/<name>-tests.md` keys the same `plans/<name>/` as `roadmaps/<name>.md`), turning spec 16's two red assertions green so tests-mode prune sweeps the directory the orchestrator actually wrote to.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (one clause, per spec)

## Tasks

### Phase 1: Fix the stem key

- [x] **Task 1: Strip the `-tests` suffix on the non-default branch of `_artifact_subdir`**
  Files: `orchestrator/main.py`
  In `_artifact_subdir` (`main.py:166-170`), the default-pair branch (`return None` for `ROADMAP.md`/`ROADMAP_TESTS.md`) stays untouched. Replace the final line `return Path(relpath).stem` with a suffix-stripped stem plus a degenerate guard:
  ```python
  stem = Path(relpath).stem.removesuffix("-tests")
  return stem or Path(relpath).stem
  ```
  Rationale (per spec 17): `-tests` is a reserved suffix — the governing spec's derivation hard-stop rejects a main-roadmap slug ending in `-tests`, so stripping never mangles a legitimate main roadmap. The `stem or ...` guard covers a file literally named `-tests.md` (stripping empties the stem) — keep the raw stem, never return `""` (an empty segment would silently alias the flat layout). Resulting contract, all four dirs keyed identically: `ROADMAP.md`/`ROADMAP_TESTS.md` → `None`; `roadmaps/<name>.md` and `roadmaps/<name>-tests.md` → `<name>`. Do NOT touch `_tests_sibling`, the default branch, `resume.py`, or the `Mode` threading — only the key value changes.
  Verify: `uv run pytest` fully green — the two spec-16 assertions (`tests/test_main.py:1099` named-tests → `kg-wmservice`, `:1104` explicit `custom-tests.md` → `custom`) turn green; default-pair, named-main (`:1094`), and track-file (`:1109`, `ROADMAP.watch.md` → `ROADMAP.watch`) assertions stay green.

### Phase 2: Docs

- [x] **Task 2: Note the shared stem in the file-protocol section** (depends on Task 1)
  Files: `docs/how-it-works.md`
  In § Файловый протокол, the per-roadmap-subdir paragraph (`how-it-works.md:49`) currently describes only the named main roadmap. Add one clause stating that the test sibling shares the main roadmap's subdirectory — `roadmaps/kg-wmservice-tests.md` keys the same `plans/kg-wmservice/` as `roadmaps/kg-wmservice.md`, exactly as the default pair shares the flat dirs (both implement- and test-mode artifacts of a named pair share one `plans/<name>/` number axis). Keep the existing prose and match the surrounding Russian.
