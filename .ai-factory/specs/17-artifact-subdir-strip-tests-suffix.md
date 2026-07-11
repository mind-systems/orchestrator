# `_artifact_subdir`: strip the `-tests` suffix — one stem keys the whole roadmap pair

Origin: `.ai-factory/handoffs/04-named-test-roadmap-stem-mismatch.md`. Ratified target (skills family: `orchestrator-artifacts` §1, `roadmap-prune` Step 5 named branch; governing spec `~/projects/skills/docs/multiuser-roadmaps.md`): a named roadmap pair shares **one** artifact-subdirectory stem, mirroring how the default pair shares the flat dirs. Depends on spec 16 (the red tests this task turns green).

## Current state

`_artifact_subdir` (`main.py:166-170`) returns `Path(relpath).stem` raw, so `roadmaps/<name>-tests.md` → `<name>-tests` while the skills family sweeps and describes `<name>`. Consequence: a tests-mode prune sweeps `plans/<name>/`+`test-runs/<name>/` and deletes nothing — the orchestrator wrote to `plans/<name>-tests/`+`test-runs/<name>-tests/`; artifacts accumulate forever, silently. Decision (2026-07-12, with the user): the orchestrator side is the one to fix — the shared-stem reading follows the default-pair analogy and is ratified in two landed skills milestones.

## Change

1. **Strip the suffix** on the non-default branch of `_artifact_subdir` (`main.py:170`):
   ```python
   stem = Path(relpath).stem.removesuffix("-tests")
   ```
   Safety is by construction: `-tests` is a reserved suffix — the governing spec's derivation hard-stop rejects a main-roadmap slug ending in `-tests`, so stripping never mangles a legitimate main roadmap (don't re-litigate). Degenerate guard: if stripping empties the stem (a file literally named `-tests.md`), keep the raw stem — never return `""` (an empty segment would silently alias the flat layout).
2. **Resulting mapping** (the cross-repo contract, verbatim from the handoff checklist): `ROADMAP.md` → `None`; `ROADMAP_TESTS.md` → `None`; `roadmaps/<name>.md` → `<name>`; `roadmaps/<name>-tests.md` → `<name>`. One stem keys all four dirs identically (`plans/`, `plan-reviews/`, `reviews/`, `test-runs/`). Implement- and test-mode artifacts of a named pair therefore share one `plans/<name>/` number axis — exactly as the default pair shares flat `plans/` (pre-13 behavior); this supersedes spec 13's sibling-subdirs sentence ("`plans/<slug>/` vs `plans/<slug>-tests/`"), which described the accidental behavior.
3. **Docs** — `docs/how-it-works.md` § Файловый протокол: one clause on the stem-keyed paragraph — the test sibling shares the main roadmap's subdirectory (`roadmaps/kg-wmservice-tests.md` → the same `plans/kg-wmservice/`).

## Files & types

- edit `orchestrator/main.py` (`_artifact_subdir`, one branch)
- edit `docs/how-it-works.md` (one clause)

## Guards

- `_tests_sibling` untouched — sibling *derivation* (`<name>-tests.md`) is correct; only the artifact *key* changes.
- Default-pair branch (`None`) untouched — byte-stable flat layout.
- `resume.py`, `Mode` threading, numbering mechanism untouched — the key value changes, the plumbing doesn't.
- The skills-side mirror (`orchestrator-artifacts` §1) already states the shared stem — after this lands, both repos agree; no skills-repo edits from here.

## Verification

- `uv run pytest` fully green — specifically the two red assertions from spec 16 (flipped named-tests mapping, explicit-path sibling) turn green; default-pair and named-main assertions stay green.
- Live: `roadmap_path: roadmaps/kg-wmservice.md`, run `test` mode → plan lands under `plans/kg-wmservice/`, runner output under `test-runs/kg-wmservice/` — same segment as the implement run's artifacts.
