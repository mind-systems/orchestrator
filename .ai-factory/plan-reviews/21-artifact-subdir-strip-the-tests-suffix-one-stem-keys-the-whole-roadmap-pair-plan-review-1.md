## Code Review Summary

**Files Reviewed:** 1 plan (targets `orchestrator/main.py`, `docs/how-it-works.md`)
**Risk Level:** 🟢 Low

### Context Gates
- **Governing spec (`.ai-factory/specs/17-artifact-subdir-strip-tests-suffix.md`)** — OK. Plan Task 1 = spec Change #1 (strip `-tests` on the non-default branch) + the degenerate-`""` guard; Task 2 = spec Change #3 (one clause in `docs/how-it-works.md` § Файловый протокол). The plan honours every Guard: `_tests_sibling`, the default `None` branch, `resume.py`, and the `Mode` threading are all explicitly left untouched.
- **Roadmap (`.ai-factory/ROADMAP.md:61`)** — OK. This is the sole `[ ]` milestone at the current seam (line 61, following the landed spec-16 tests-first pin at line 59). Plan title and intent match the roadmap line verbatim, and it correctly supersedes spec 13's sibling-subdirs sentence.
- **Architecture / Rules** — no `.ai-factory/ARCHITECTURE.md`/`RULES.md` boundary concerns; all code change stays in the `main.py` orchestration layer, consistent with the sibling helpers `_tests_sibling`/`_resolve_roadmap_relpath`.

### Critical Issues
None.

### Verification of plan against ground truth
- **`main.py:166-170`** — confirmed. `_artifact_subdir` today returns `Path(relpath).stem` raw on line 170; the default-pair branch (`return None`) is lines 168-169. The plan's line references and untouched-branch claim are accurate.
- **Proposed code** — correct on all six mappings the plan enumerates:
  - `ROADMAP.md`/`ROADMAP_TESTS.md` → `None` (default branch untouched).
  - `roadmaps/kg-wmservice.md` → stem `kg-wmservice`, no `-tests` suffix → `kg-wmservice` (stays green, `test_main.py:1094`).
  - `roadmaps/kg-wmservice-tests.md` → `kg-wmservice` (turns spec-16 red green, `:1099`).
  - `custom-tests.md` → `custom` (turns spec-16 red green, `:1104`).
  - `ROADMAP.watch.md` → stem `ROADMAP.watch`, `.removesuffix("-tests")` is a no-op → `ROADMAP.watch` (stays green, `:1109`).
  - degenerate `-tests.md` → stem `-tests` → stripped to `""` → guard returns raw `-tests` (never an empty aliasing segment).
- **`stem or Path(relpath).stem` guard** — the plan spells out the two-line form that the spec describes prose-only; a correct, faithful expansion. `str.removesuffix` is 3.9+ and the project pins `requires-python >= 3.11`, so no compatibility concern.
- **`docs/how-it-works.md:49`** — confirmed. The per-roadmap-subdir paragraph in § Файловый протокол currently describes only the named main roadmap (`plans/kg-wmservice/`, `reviews/kg-wmservice/`); Task 2's added clause about the shared test-sibling stem fits it exactly, and the "match the surrounding Russian" instruction is appropriate.

### Positive Notes
- Task boundaries are clean: the code fix (Task 1) is independently verifiable via `uv run pytest`, and the docs clause (Task 2) correctly declares its `depends on Task 1`.
- The plan restates the safety-by-construction rationale (reserved `-tests` suffix, derivation hard-stop) and explicitly says "do not re-litigate", keeping the implementer from re-deriving a settled decision.
- Verification section pins exact test lines and the green/red split, matching the spec's own acceptance criteria.

PLAN_REVIEW_PASS
