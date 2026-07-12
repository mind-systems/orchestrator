# Review: Tests-first: pin the shared artifact stem for a named test roadmap

## Scope
Tests-only milestone. `git status` confirms the only source change is `tests/test_main.py` (the other staged files are planning artifacts). `orchestrator/main.py` is untouched, satisfying the "no production code" guard from spec 16.

## Changes reviewed
`tests/test_main.py`, `_artifact_subdir` block:
1. `test_artifact_subdir_named_tests_roadmap_uses_stem` — assertion flipped from `"kg-wmservice-tests"` to `"kg-wmservice"`, docstring updated to state the shared stem (one stem per roadmap pair). This is the deliberate Class-A pin flip described in spec 16 §1.
2. New `test_artifact_subdir_explicit_path_tests_sibling_uses_stem` — asserts `_artifact_subdir("custom-tests.md") == "custom"`, the explicit-path sibling case (spec 16 §2). Placed directly after Task 1's test, follows the neighbouring one-assert-with-docstring pattern.

## Correctness
- The two new assertions match the ratified cross-repo contract (shared `<name>` stem for a named roadmap pair) verbatim; values and paths are exactly as specified.
- Ran `uv run pytest tests/test_main.py -k artifact_subdir`: **2 failed, 4 passed** — precisely the spec's expected outcome. The two failures are exactly the flipped named-tests case and the new explicit-path case; both fail because production `_artifact_subdir` still returns the raw stem (`kg-wmservice-tests` / `custom-tests`). These reds are **by design** — they turn green when spec 17 applies `.removesuffix("-tests")`. This is the repo's established 07→05 red-until-fix TDD pattern, not a defect.
- Green-must-stay assertions verified intact: default `ROADMAP.md`/`ROADMAP_TESTS.md` → `None`, named-main `roadmaps/kg-wmservice.md` → `"kg-wmservice"`, and track-file `ROADMAP.watch.md` → `"ROADMAP.watch"` all pass.

## Bugs / security / correctness problems
None. The change is a scoped test edit with no runtime, type, migration, or concurrency surface. The intentional failures align with the milestone's stated TDD design and do not represent a real defect.

REVIEW_PASS
