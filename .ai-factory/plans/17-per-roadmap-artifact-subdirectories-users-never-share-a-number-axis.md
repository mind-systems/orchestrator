# Plan: Per-roadmap artifact subdirectories — users never share a number axis

## Context
Route each named roadmap's artifacts (`plans/`, `plan-reviews/`, `reviews/`, `test-runs/`) into a per-roadmap subdirectory keyed by the roadmap file's stem, so concurrent developers never collide on the `NN` number axis after their milestone commits merge — while the default `ROADMAP.md` / `ROADMAP_TESTS.md` pair stays byte-stable flat.

## Settings
- Testing: yes
- Logging: minimal
- Docs: yes

## Tasks

### Phase 1: Subdirectory key and threading (code)

- [x] **Task 1: Add `_artifact_subdir` helper and `Mode.artifact_subdir` field**
  Files: `orchestrator/main.py`
  Add a pure helper `def _artifact_subdir(relpath: str) -> str | None` near the other resolution helpers (after `_tests_sibling`, `main.py:157-162`). Mapping per spec `.ai-factory/specs/13-artifact-subdirs.md` §Change.1: the default pair `"ROADMAP.md"` and `"ROADMAP_TESTS.md"` → `None` (flat); anything else → the roadmap file's stem via `Path(relpath).stem` (`roadmaps/kg-wmservice.md` → `"kg-wmservice"`, `roadmaps/kg-wmservice-tests.md` → `"kg-wmservice-tests"`, `ROADMAP.watch.md` → `"ROADMAP.watch"`). Add a new field to the `Mode` NamedTuple (`main.py:24-38`): `artifact_subdir: str | None = None` (place it as the last field so it carries a default and the existing positional `IMPLEMENT_MODE`/`TEST_MODE` literals at `main.py:41-71` remain valid unchanged). Key comes only from the resolved relpath — no git identity.

- [x] **Task 2: Apply the subdirectory segment to artifact dirs in `process_milestone`** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `process_milestone` (`main.py:186-195`), after computing `plans_dir`, `output_dir`, and `plan_reviews_dir`, insert the subdir segment when `mode.artifact_subdir` is set: `plans_dir = ai_factory / "plans" / mode.artifact_subdir`, `output_dir = ai_factory / mode.output_dirname / mode.artifact_subdir`, `plan_reviews_dir = ai_factory / "plan-reviews" / mode.artifact_subdir` (leave the flat paths untouched when it is `None`). The existing `mkdir(parents=True, exist_ok=True)` calls already create nested dirs. `_detect_step` (called `main.py:204`) then receives the subdir'd `plan_path.parent`, `plan_reviews_dir`, and `output_dir` through its existing parameters — no signature change; `resume.py` untouched.

- [x] **Task 3: Thread the subdir into `_run_dynamic_loop` and set it in both loop setups** (depends on Task 1)
  Files: `orchestrator/main.py`
  `_run_dynamic_loop` (`main.py:348-399`) builds its own `plans_dir` (`main.py:350-351`) and calls `_next_number(plans_dir)` (`main.py:386`) — this must count within the same subdir the plan is written to, or numbering restarts inconsistently. Add an `artifact_subdir: str | None = None` parameter to `_run_dynamic_loop`; when set, build `plans_dir = project_dir / ".ai-factory" / "plans" / artifact_subdir` (keep `mkdir(parents=True, exist_ok=True)`). In `_test_loop` (`main.py:410-414`) and `_implement_loop` (`main.py:424-428`), set `artifact_subdir=_artifact_subdir(relpath)` inside the existing `mode = ..._replace(...)` call, and pass `mode.artifact_subdir` as the new argument to `_run_dynamic_loop`. Byte-stable default: for `ROADMAP.md`/`ROADMAP_TESTS.md` the key is `None`, so `plans_dir` and every artifact path are identical to today.

### Phase 2: Tests

- [x] **Task 4: Unit tests for the key mapping plus a subdir'd resume-dispatch test** (depends on Task 1, Task 2)
  Files: `tests/test_main.py`
  Add unit tests pinning `_artifact_subdir` (import it alongside the existing `_resolve_roadmap_relpath`/`_tests_sibling` imports, `test_main.py:17-18`): `"ROADMAP.md"` → `None`, `"ROADMAP_TESTS.md"` → `None`, `"roadmaps/kg-wmservice.md"` → `"kg-wmservice"`, `"roadmaps/kg-wmservice-tests.md"` → `"kg-wmservice-tests"` (the four mappings the spec §Change.4 requires; optionally also `"ROADMAP.watch.md"` → `"ROADMAP.watch"`). Add one integration-shaped test reusing the existing `_dms_dirs` fixture pattern (`test_main.py:217-229`) but with the artifact dirs nested one level deeper (e.g. `plans/kg-wmservice/`): assert `_detect_milestone_step` dispatches identically to the flat case for at least one representative step (the detector's contract is dirs-in/dispatch-out, so pointing the fixture one level deeper must not change the result). Do not restructure existing tests.

### Phase 3: Docs

- [x] **Task 5: Document the per-roadmap subdirectory layout** (depends on Task 1)
  Files: `docs/how-it-works.md`, `CLAUDE.md`
  In `docs/how-it-works.md` — the "Файловый протокол" paragraph (`how-it-works.md:43-45`) and the resume/sidecar sentence naming `.ai-factory/plans/{NN}-{slug}.json` (`how-it-works.md:23`) — state (in Russian, matching the file) that artifact dirs are flat for the default `ROADMAP.md`/`ROADMAP_TESTS.md` pair, and that any other (named) roadmap routes its artifacts into a per-roadmap subdirectory keyed by the roadmap file's stem (e.g. `plans/kg-wmservice/`, `reviews/kg-wmservice/`). In `CLAUDE.md`, update the file-protocol line listing output dirs (`CLAUDE.md:72`) to note the same flat-default / per-roadmap-subdir behavior. Do NOT touch the skills repo — `orchestrator-artifacts` and `roadmap-prune` mirrors are separate skills-repo tasks (spec §Guards).

## Commit Plan
- **Commit 1** (after tasks 1-3): "Route named-roadmap artifacts into per-roadmap subdirectories"
- **Commit 2** (after task 4): "Pin artifact-subdir key mapping and subdir resume dispatch"
- **Commit 3** (after task 5): "Document per-roadmap artifact subdirectory layout"
