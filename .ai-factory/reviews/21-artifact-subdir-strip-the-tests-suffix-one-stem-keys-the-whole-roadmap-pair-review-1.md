# Review: `_artifact_subdir`: strip the `-tests` suffix — one stem keys the whole roadmap pair

## Scope
Code changes: `orchestrator/main.py` (`_artifact_subdir`, one branch) and `docs/how-it-works.md` (one clause). Reviewed against plan `21-...` and spec `.ai-factory/specs/17-artifact-subdir-strip-tests-suffix.md`.

## Verification

- `uv run pytest` — 123 passed. Spec-16's two red assertions turn green (`roadmaps/kg-wmservice-tests.md` → `kg-wmservice`; `custom-tests.md` → `custom`); default-pair, named-main, and track-file assertions stay green.

## Correctness walkthrough

`_artifact_subdir` now returns `Path(relpath).stem.removesuffix("-tests") or Path(relpath).stem` on the non-default branch. Traced every branch:

- Default pair `ROADMAP.md`/`ROADMAP_TESTS.md` → `None` (branch untouched, byte-stable).
- `roadmaps/kg-wmservice.md` → stem has no `-tests` suffix → `kg-wmservice` (unchanged).
- `roadmaps/kg-wmservice-tests.md` → stripped → `kg-wmservice` (shares the main's subdir).
- Explicit `custom-tests.md` → `custom`.
- Degenerate `-tests.md` → stem `-tests` → strips to `""` → `or` guard returns raw `-tests`; never an empty segment that would alias the flat layout.
- `ROADMAP.watch.md` → `Path.stem` strips only the final `.md` → `ROADMAP.watch`, no `-tests` suffix → unchanged.

**Runtime contract holds across both callers.** `_implement_loop` resolves `roadmaps/<name>.md` → subdir `<name>`; `_test_loop` derives the sibling `roadmaps/<name>-tests.md` (via untouched `_tests_sibling`) then keys it → same subdir `<name>`. Both modes now write under `plans/<name>/`, and `_next_number` picks `max(NN)+1` over the shared glob, so implement- and test-mode artifacts interleave on one number axis — exactly the intended shared-axis contract, mirroring the default flat pair. No collision, no resume regression: `resume.py` and the `Mode` threading are untouched and receive the subdir'd paths through the existing params.

**Reserved-suffix assumption is respected, not re-litigated.** A main roadmap legitimately ending in `-tests` is excluded by the governing spec's derivation hard-stop; the code correctly relies on that invariant rather than re-checking it. Out of scope per the spec.

## Docs

The added clause in § Файловый протокол is accurate, in Russian, and matches the surrounding prose. It correctly states the test sibling shares the main roadmap's subdirectory and one `plans/<name>/` number axis.

## Findings

None. The change is minimal, matches the plan and spec exactly, and all guards behave as specified.

REVIEW_PASS
