# Plan: Roadmap-path setting — named roadmaps through the `roadmap_filename` seam

## Context
Let the orchestrator take its roadmap from a per-workstation `orchestrator.json` setting with three explicit states (absent → default `ROADMAP.md`; `"my"` → identity-derived named roadmap under `roadmaps/<slug>.md` with owner-line verification; any other value → an explicit relative path used verbatim), widening the existing `roadmap_filename` seam from filename to relative-path semantics. Byte-stable default is the hard acceptance criterion: with no `roadmap_path` key, every run is behavior-identical to today.

## Settings
- Testing: yes (spec mandates unit tests — all new surfaces fail silently)
- Logging: minimal
- Docs: yes (spec step 7)

## Tasks

### Phase 1: Config key

- [x] **Task 1: Add `roadmap_path` to `OrchestratorConfig` with a load-time guard**
  Files: `orchestrator/config.py`
  Add optional field `roadmap_path: str | None = None` to `OrchestratorConfig` (NOT in `required`). In `load_config`, read it via `data.get("roadmap_path") or None`. Add a loud guard: if the value is set and is an absolute path (`Path(value).is_absolute()`) or contains any `..` segment (`".." in Path(value).parts`), raise `SystemExit` naming the offending value (mirror the existing `SystemExit` message style in this file). No owner check or derivation here — this is a pure string/path-shape guard; the three-state semantics live in `main.py` (Task 3). Do not add the key to `orchestrator.json.example` (home is the per-workstation gitignored `orchestrator.json`, and the default is absence).

### Phase 2: Resolution helpers (main.py)

- [x] **Task 2: Pure `_derive_identity_slug` helper**
  Files: `orchestrator/main.py`
  Add `_derive_identity_slug(email: str | None, name: str | None) -> str | None`: slug from the email local-part (portion before `@`), lowercased, with every run of non-alphanumeric characters collapsed to a single hyphen and leading/trailing hyphens stripped (`kg.wmservice@gmail.com` → `kg-wmservice`, per the spec's canonical example). If email is empty/None, fall back to slugifying `name` the same way. If both are empty/None → return `None` (derivation failure). Keep it pure (no git calls) so it is unit-testable in isolation.

- [x] **Task 3: `_resolve_roadmap_relpath` and `_tests_sibling` helpers** (depends on Task 1, Task 2)
  Files: `orchestrator/main.py`
  Add `_resolve_roadmap_relpath(config, project_dir) -> str` implementing the three disjoint states keyed on `config.roadmap_path`:
  - **`None` (absent)** → return `"ROADMAP.md"` (byte-stable).
  - **`"my"`** → read `git config user.email` / `git config user.name` (via `subprocess.run` in `project_dir`; treat non-zero / empty as `None`), call `_derive_identity_slug`. Slug is `None` → raise `HaltError` telling the user to set git identity or pass an explicit path (spec "Pinned forks"). Otherwise target `f"roadmaps/{slug}.md"`; if the file is missing under `.ai-factory/`, print one loud fallback line stating the derived path and that it falls back, and return `"ROADMAP.md"` (lazy migration). If present, verify the file's first line is exactly `> Owner: <email>` matching the current git email — mismatch or malformed first line → raise `HaltError` naming the owner (operational stop; `HaltError` is already imported at `main.py:13`). Return the named relpath.
  - **any other value** → return it verbatim (explicit path, no owner check).
  Also add pure `_tests_sibling(relpath: str) -> str`: exact `"ROADMAP.md"` → `"ROADMAP_TESTS.md"` (the default pair is a named special case, NOT `-tests` suffixing); anything else → same directory, stem + `"-tests.md"` (`roadmaps/kg-wmservice.md` → `roadmaps/kg-wmservice-tests.md`). Use `pathlib` for stem/parent so nested paths work.

### Phase 3: Widen the seam

- [x] **Task 4: Rename `roadmap_filename` → `roadmap_relpath` across `Mode`** (depends on Task 3)
  Files: `orchestrator/main.py`
  Rename the `Mode` field `roadmap_filename` → `roadmap_relpath` (`main.py:26`), documenting the new semantics in the field comment: *path relative to `.ai-factory/`*. Update both mode instances (`IMPLEMENT_MODE` `main.py:41`, `TEST_MODE` `main.py:57`) and the join in `process_milestone` (`main.py:126`, `project_dir / ".ai-factory" / mode.roadmap_relpath`). The join code is unchanged — it already accepts a multi-segment relative path. Verify no `roadmap_filename` references remain (`grep -n roadmap_filename orchestrator/` → zero hits).

- [x] **Task 5: Wire the loops to resolve the relpath** (depends on Task 4)
  Files: `orchestrator/main.py`
  `_implement_loop` (`main.py:344`): rename its `roadmap_filename` parameter → `roadmap_relpath: str | None = None`; inside, resolve `relpath = roadmap_relpath or _resolve_roadmap_relpath(config, project_dir)` (explicit argument → setting → default). Build `roadmap_path = project_dir / ".ai-factory" / relpath`; generalize the missing-file message from `"ERROR: No ROADMAP.md found at {roadmap_path}"` to `f"ERROR: No roadmap found at {roadmap_path}"`. Use `IMPLEMENT_MODE._replace(planner_prompt_name=planner_prompt_name, roadmap_relpath=relpath)`.
  `_test_loop` (`main.py:331`): resolve the main relpath exactly as above (`_resolve_roadmap_relpath(config, project_dir)`, including `"my"` derivation and its fallback), derive `sibling = _tests_sibling(main_relpath)`, build `roadmap_path` from the sibling, generalize the missing-file message the same way, and use `TEST_MODE._replace(roadmap_relpath=sibling)`. The sibling is always derived from the roadmap in play — never configured independently.

- [x] **Task 6: Widen the two roadmap-name hardcodes in `reviewer.md`** (depends on Task 5)
  Files: `orchestrator/prompts/reviewer.md`
  Wording-only edits. Milestone-alignment gate (`reviewer.md:23`): replace the fixed `.ai-factory/ROADMAP.md` reference with "the roadmap in play — `.ai-factory/ROADMAP.md` or a named roadmap under `.ai-factory/roadmaps/`". Root-recovery gate (`reviewer.md:25`): widen the plan-title match target to `.ai-factory/ROADMAP.md`, `.ai-factory/ROADMAP_TESTS.md`, **or any `.ai-factory/roadmaps/*.md`` (the `roadmaps/` directory is the sanctioned enumeration point). Keep the gate's skip-if-no-match tail intact.

### Phase 4: Tests & docs

- [x] **Task 7: Unit tests for every new pure surface** (depends on Task 5)
  Files: `tests/test_main.py`, `tests/test_config.py` (new)
  Follow the existing `tests/test_main.py` conventions (pytest, `tmp_path`, direct imports from `orchestrator.main`). Add tests for:
  - `_derive_identity_slug`: canonical example (`kg.wmservice@gmail.com` → `kg-wmservice`), punctuation runs collapse to single hyphen, empty email → name fallback, both empty → `None`.
  - Owner-line gate / three-state resolution of `_resolve_roadmap_relpath` (monkeypatch or stub the git-config reads; create the roadmap file under a `tmp_path/.ai-factory`): absent → `"ROADMAP.md"`; `"my"` + file present + matching owner → the named relpath; `"my"` + file missing → `"ROADMAP.md"` (fallback); `"my"` + owner mismatch/malformed first line → `HaltError`; `"my"` + derivation failure → `HaltError`; explicit value → returned verbatim (no owner check).
  - `_tests_sibling`: `"ROADMAP.md"` → `"ROADMAP_TESTS.md"`; `"roadmaps/kg-wmservice.md"` → `"roadmaps/kg-wmservice-tests.md"`.
  - Config loading (new `tests/test_config.py`, or extend existing if a config test home exists): absent key → `roadmap_path is None`; value passes through; absolute path or `..` segment → `SystemExit`. Use `ORCHESTRATOR_CONFIG` env override pointing at a temp JSON file.
  Do not restructure existing tests; the pre-change pytest suite must stay green.

- [x] **Task 8: Docs — `roadmap_path` key and named-roadmap target** (depends on Task 5)
  Files: `docs/configuration.md`, `docs/target-project.md`
  `docs/configuration.md`: document the `roadmap_path` key with all three states (absent → default; `"my"` → identity-derived named roadmap with owner verification and loud fallback when missing; explicit relative path → used verbatim, no owner check) and the absolute/`..` guard. `docs/target-project.md`: add one paragraph — a named roadmap under `.ai-factory/roadmaps/` may be the target, selected by this setting. Describe behavior, not code; match the language of the neighboring docs.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Add roadmap_path config key and resolution helpers"
- **Commit 2** (after tasks 4-6): "Widen the roadmap seam to relative paths and named roadmaps"
- **Commit 3** (after tasks 7-8): "Cover roadmap-path resolution with tests and docs"
