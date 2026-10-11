# Plan: 29.6 — named-roadmap resolution lives in `layout.py`

## Context
Move named-roadmap resolution out of `main.py` into a new adapter module, `orchestrator/layout.py`. The moved names are `_USER_SLUG_SCRIPT`, `_git_config_value`, `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir`. After the move, `main.py` holds only the flow, the composition root and the CLI. The change is behaviour-neutral and adds no new test. Spec: `.ai-factory/specs/trickster77777/0073-named-roadmap-resolution-lives-in-layout.md`. Governing spec: `.ai-factory/ARCHITECTURE.md`. Its § Dependency Rules puts `layout.py` in the "Roles and adapters" layer, and `main` (the composition root) may import it. Adapters import only from the vocabulary below them, which here means `errors` and `config`. Its § Folder Structure gives `layout.py` as "Adapter: named-roadmap resolution at assembly".

Notes from the code (baseline: `uv run pytest` → 227 passed):
- Every moved name sits in one contiguous block of `main.py`, between `_next_number` and `_artifact_dir`.
- After the move, `main.py` still uses `subprocess` (`_git_commit`, `process_task`), `Path`, `HaltError` (the plan-review guard in `process_task` and `cli`'s `except HaltError`), and `OrchestratorConfig`. None of its imports go.
- Inside `main.py`, only `_test_loop` and `_implement_loop` call the moved names, and those call sites stay textually unchanged.
- No doc, `CLAUDE.md` included, names the current home of these functions. `ARCHITECTURE.md` already names `layout.py`, so no doc changes.
- No test patches `main_module._resolve_roadmap_relpath`, `_tests_sibling` or `_artifact_subdir`. The only patches to move are the ones the spec lists.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Adapter module

- [x] **Create `orchestrator/layout.py` with named-roadmap resolution**
  Files: `orchestrator/layout.py`
  Follow the header shape of the sibling modules (`errors.py`, `protocol.py`, `claude_cli.py`). Start with a one-line module docstring, e.g. `"""Named-roadmap resolution at assembly: the roadmap in play, its test sibling, and the per-roadmap artifact subdirectory."""`, then `from __future__ import annotations`. Then the stdlib imports `import subprocess` and `from pathlib import Path`. Then exactly two package imports: `from .config import OrchestratorConfig` and `from .errors import HaltError`, and nothing else from the package.
  Move these from `main.py` verbatim, in their current order, with bodies, docstrings, messages and the module-level value unchanged:
  - `_USER_SLUG_SCRIPT = Path.home() / ".claude" / "skills" / "roadmap-engine" / "scripts" / "user-slug.sh"`
  - `_git_config_value(project_dir: Path, key: str) -> str | None`
  - `_resolve_roadmap_relpath(config: OrchestratorConfig, project_dir: Path) -> str`, with every `HaltError` message unchanged
  - `_tests_sibling(relpath: str) -> str`
  - `_artifact_subdir(relpath: str) -> str | None`
  `_resolve_roadmap_relpath` must keep reading `_USER_SLUG_SCRIPT` and calling `subprocess.run` through module-level lookups in `layout`, so the tests can patch `layout._USER_SLUG_SCRIPT` and `layout.subprocess.run`.

### Rewire the importer

- [x] **Strip the moved block from `main.py` and import from `layout`** (depends on Create `orchestrator/layout.py`)
  Files: `orchestrator/main.py`
  Delete the five moved definitions, which form the block between `_next_number` and `_artifact_dir`. Keep two blank lines between the remaining top-level definitions. Add `from .layout import _artifact_subdir, _resolve_roadmap_relpath, _tests_sibling` in alphabetical position among the package imports, after `.errors` and before `.notify`. Do not import `_USER_SLUG_SCRIPT` or `_git_config_value` into `main`, because nothing in `main` uses them. Keep every existing import: `subprocess`, `Path`, `HaltError` and `OrchestratorConfig` are all still used. The call sites in `_test_loop` and `_implement_loop` stay textually unchanged.

### Tests follow the owner

- [x] **Point the resolution tests at `layout`** (depends on Strip the moved block from `main.py`)
  Files: `tests/test_main.py`
  - Imports: add `from orchestrator import layout as layout_module` beside the existing `from orchestrator import main as main_module`, following the `errors as errors_module` pattern. Remove `_artifact_subdir`, `_resolve_roadmap_relpath` and `_tests_sibling` from the `from orchestrator.main import (...)` block, and add `from orchestrator.layout import _artifact_subdir, _resolve_roadmap_relpath, _tests_sibling`.
  - `_install_slug_script` and `test_resolve_roadmap_relpath_my_missing_script_raises_halt`: `monkeypatch.setattr(main_module, "_USER_SLUG_SCRIPT", …)` → `monkeypatch.setattr(layout_module, "_USER_SLUG_SCRIPT", …)`.
  - Every `test_resolve_roadmap_relpath_my_*` test: `main_module.subprocess` → `layout_module.subprocess`, in both the single-line `monkeypatch.setattr(main_module.subprocess, "run", …)` form and the multi-line `monkeypatch.setattr(\n    main_module.subprocess, "run", …)` form. This covers the missing-script, script-failure and not-executable tests.
  - Leave everything else unchanged: `_fake_git_config`, `_config_with_roadmap_path`, the `_tests_sibling`/`_artifact_subdir` test bodies, the section comments, and every other `main_module` patch (`load_config`, `run_implement`, `report`, the roles, `mark_done`, `_git_commit`). No test is added, removed or reworded.
  - Verify: `grep -nE 'main_module(\.subprocess|, "_USER_SLUG_SCRIPT")' tests/` returns no matches, and neither does `grep -nE '_USER_SLUG_SCRIPT|_git_config_value|def _resolve_roadmap_relpath|def _tests_sibling|def _artifact_subdir' orchestrator/main.py`. `uv run pytest` passes with 227 tests, the same count as before.
