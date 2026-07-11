# Tests-first: pin the shared artifact stem for a named test roadmap (red until the fix)

Origin: `.ai-factory/handoffs/04-named-test-roadmap-stem-mismatch.md` — cross-repo verification found the orchestrator and the skills family pin opposite artifact-subdirectory stems for a named test roadmap. Ratified target (skills side, two landed milestones 4.6/4.7 + `orchestrator-artifacts` §1): **one stem keys the whole roadmap pair** — `roadmaps/<name>-tests.md` shares `<name>`, never `<name>-tests`. The TDD half of the fix chain; the implementation is the next task (spec 17).

## Current state

`_artifact_subdir` (`main.py:166-170`) returns `Path(relpath).stem` raw on its non-default branch, so `roadmaps/kg-wmservice-tests.md` → `kg-wmservice-tests`. The existing unit test `test_artifact_subdir_named_tests_roadmap_uses_stem` (`tests/test_main.py:1097-1099`) pins exactly this raw mapping — but that behavior fell out of the implementation and was never a decision (task 13's contract said "the roadmap file's stem" without deciding the test-sibling case). Per the test-philosophy corollary this pin is Class A in spirit: it froze accidental behavior, not a designed one — it gets flipped, not preserved.

The surface is silent-failure grade: with the raw stem, an orchestrator test run on a named roadmap writes `plans/<name>-tests/…` and `test-runs/<name>-tests/…`, while a tests-mode prune (skills side) sweeps `plans/<name>/…` and `test-runs/<name>/…` — the sweep deletes nothing, artifacts accumulate forever, nothing ever crashes.

## Change

Tests only — `tests/test_main.py`, the `_artifact_subdir` block (`:1078-1099`):

1. **Flip** `test_artifact_subdir_named_tests_roadmap_uses_stem`: assert `_artifact_subdir("roadmaps/kg-wmservice-tests.md") == "kg-wmservice"` — **red** until spec 17 lands, by design (the repo's landed 07→05 pattern).
2. **Add** the explicit-path sibling case: `_artifact_subdir("custom-tests.md") == "custom"` (an explicit non-`roadmaps/` roadmap's test sibling shares its stem the same way) — red until 17.
3. **Keep green**: the default pair (`ROADMAP.md`/`ROADMAP_TESTS.md` → `None`) and the named main roadmap (`roadmaps/kg-wmservice.md` → `"kg-wmservice"`) assertions stay untouched and must stay green through both tasks.

## Files & types

- edit `tests/test_main.py` only.

## Guards

- No production code in this task — `orchestrator/main.py` untouched; the suite is knowingly red on exactly the two flipped/added assertions until spec 17.
- Do not "fix" the red by weakening assertions — the target mapping is ratified cross-repo (don't re-litigate; the `-tests` suffix is reserved by the governing spec's derivation hard-stop, so stripping is safe by construction).

## Verification

- `uv run pytest tests/test_main.py -k artifact_subdir` → exactly two red (the flipped named-tests case, the new explicit-path case), rest green.
