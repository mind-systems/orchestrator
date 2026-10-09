# Plan: 25.2 — artifact directories derive in one place

## Context
`process_task` and `_run_dynamic_loop` in `orchestrator/main.py` each join `mode.artifact_subdir` / an `artifact_subdir` argument onto artifact directories by hand, so the layout choice is held twice. Add one derivation, `_artifact_dir(project_dir, mode, dirname)`, build every artifact directory from it, and make `_run_dynamic_loop` read the subdirectory from the mode — behaviour-neutral, including when directories get created (spec: `.ai-factory/specs/trickster77777/0061-artifact-directories-derive-in-one-place.md`; governing: `.ai-factory/ARCHITECTURE.md` § What varies (Layout), § Composition root).

## Settings
- Testing: yes (one test group required by the spec)
- Logging: none
- Docs: no

## Tasks

### Derive artifact directories in one place

- [x] **Add `_artifact_dir`**
  Files: `orchestrator/main.py`
  Add `def _artifact_dir(project_dir: Path, mode: Mode, dirname: str) -> Path` next to `_artifact_subdir` (it must come after the `Mode` class, which is defined at the top of the module, so placing it right after `_artifact_subdir` works). It returns `project_dir / ".ai-factory" / dirname`, joined with `mode.artifact_subdir` when that is truthy (same truthiness test as today's `if mode.artifact_subdir:`). Pure path computation: it must NOT create any directory. One-line docstring in the style of `_artifact_subdir` (behaviour only, no plan/roadmap references).

- [x] **`process_task` builds its directories from `_artifact_dir`** (depends on Add `_artifact_dir`)
  Files: `orchestrator/main.py`
  In `process_task`, replace the `ai_factory` local, the three hand-built paths and the `if mode.artifact_subdir:` join block with:
  `plans_dir = _artifact_dir(project_dir, mode, "plans")`, `output_dir = _artifact_dir(project_dir, mode, mode.verify.output_dirname)`, `plan_reviews_dir = _artifact_dir(project_dir, mode, "plan-reviews")`. The `ai_factory` local has no other use, so remove it. Keep the three `mkdir(parents=True, exist_ok=True)` calls exactly as they are, in the same order and position. Leave `roadmap_path = project_dir / ".ai-factory" / mode.roadmap_relpath` untouched — it is a roadmap path, not an artifact directory.

- [x] **`_run_dynamic_loop` takes the mode** (depends on Add `_artifact_dir`)
  Files: `orchestrator/main.py`
  Change the signature to `_run_dynamic_loop(project_dir: Path, roadmap_path: Path, config: OrchestratorConfig, process_fn, mode: Mode) -> None` — `mode` replaces `artifact_subdir: str | None = None`, with no default (both callers pass it). Replace the hand-built `plans_dir` and its `if artifact_subdir:` join with `plans_dir = _artifact_dir(project_dir, mode, "plans")`; keep `plans_dir.mkdir(parents=True, exist_ok=True)` where it is — it still creates only the plans directory. `_next_number(plans_dir)` stays unchanged.
  In `_test_loop` and `_implement_loop`, replace the `artifact_subdir=mode.artifact_subdir,` argument with `mode=mode,`. The `_replace(..., artifact_subdir=_artifact_subdir(relpath))` assembly stays as is. No other caller of `_run_dynamic_loop` exists (`notify.py` only mentions it in comments).

### Test

- [x] **Test `_artifact_dir`** (depends on Add `_artifact_dir`)
  Files: `tests/test_main.py`
  Import `_artifact_dir`, `IMPLEMENT_MODE` and `TEST_MODE` from `orchestrator.main` (add to the existing alphabetised `from orchestrator.main import (...)` block). Add a section after the `_artifact_subdir` tests, with the same `# ---` banner style and one-line "Should …" docstrings, using `tmp_path` as the project directory:
  - a mode without a subdirectory (`IMPLEMENT_MODE`) → `_artifact_dir(tmp_path, IMPLEMENT_MODE, "plans") == tmp_path / ".ai-factory" / "plans"`;
  - `IMPLEMENT_MODE._replace(artifact_subdir="john-doe")` → `tmp_path / ".ai-factory" / "plans" / "john-doe"`;
  - `TEST_MODE` with `TEST_MODE.verify.output_dirname` → `tmp_path / ".ai-factory" / "test-runs"` (assert against the literal `"test-runs"` path so a changed dirname is caught).
  Optionally assert the returned directory does not exist afterwards (the function does not create it). Do not touch the existing `_artifact_subdir` tests. Run `uv run pytest` and confirm the whole suite passes.
