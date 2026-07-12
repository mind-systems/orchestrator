# Plan: Tests-first: pin the shared artifact stem for a named test roadmap

## Context
Flip the `_artifact_subdir` unit test to pin the ratified cross-repo contract — a named roadmap pair (`roadmaps/<name>.md` + `roadmaps/<name>-tests.md`) shares one artifact stem `<name>` — and add the explicit-path sibling case. Per spec 16, both new assertions are knowingly **red** until spec 17 lands the production fix; the default-pair and named-main assertions stay green.

## Settings
- Testing: yes (tests-only milestone, per spec 16)
- Logging: none
- Docs: no

## Tasks

### Phase 1: Pin the shared test stem

- [x] **Task 1: Flip the named-test-roadmap assertion to the shared stem**
  Files: `tests/test_main.py`
  In `test_artifact_subdir_named_tests_roadmap_uses_stem` (currently at `:1097-1099`), change the assertion from `_artifact_subdir("roadmaps/kg-wmservice-tests.md") == "kg-wmservice-tests"` to `== "kg-wmservice"`, and update the docstring to state that a named test-roadmap shares its main roadmap's stem (one stem per roadmap pair). This is a deliberate flip of a Class-A accidental pin — the raw-stem behavior was never a decision. The assertion is **red** until spec 17 strips the `-tests` suffix in `_artifact_subdir`; that is by design (the repo's landed 07→05 red-until-fix pattern).

- [x] **Task 2: Add the explicit-path test-sibling case**
  Files: `tests/test_main.py`
  Add a new test function (e.g. `test_artifact_subdir_explicit_path_tests_sibling_uses_stem`) directly after Task 1's test, asserting `_artifact_subdir("custom-tests.md") == "custom"` — an explicit, non-`roadmaps/` roadmap's test sibling shares its stem the same way. Follow the existing one-assert-with-docstring pattern of the neighbouring `_artifact_subdir` tests. Also **red** until spec 17.

## Verification
- `uv run pytest tests/test_main.py -k artifact_subdir` → exactly two red (the flipped named-tests case, the new explicit-path case); the default-pair (`ROADMAP.md`/`ROADMAP_TESTS.md` → `None`), named-main (`roadmaps/kg-wmservice.md` → `"kg-wmservice"`), and track-file assertions stay green.
- `orchestrator/main.py` must remain untouched (no production code in this task).
