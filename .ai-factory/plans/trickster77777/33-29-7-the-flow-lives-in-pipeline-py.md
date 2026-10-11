# Plan: 29.7 — the flow lives in `pipeline.py`

## Context
Move the flow out of `main.py` into a new `orchestrator/pipeline.py`: `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task` and `_run_dynamic_loop`. Delete `_run_loop`, which nothing calls. After the move, `main.py` is the composition root and the CLI only (`_implement_loop`, `_test_loop`, `run_implement`, `run_test`, `cli`) and stays the `orchestrator.main:cli` entry point. The change is behaviour-neutral and adds no new test. Spec: `.ai-factory/specs/trickster77777/0074-the-flow-lives-in-pipeline.md`. Governing spec: `.ai-factory/ARCHITECTURE.md`. Its § Dependency Rules puts `pipeline.py` in "The flow" layer, below `main` and above roles/adapters and vocabulary, with `pipeline` → `resume` as the one named in-layer edge. Its § Folder Structure already names `pipeline.py`, and § The one flow already puts `process_task` and `Mode` there, so no doc changes.

Notes from the code (baseline: `uv run pytest` → 227 passed):
- The spec says `main` imports `IMPLEMENT_MODE`, `TEST_MODE` and `_run_dynamic_loop` from `pipeline`. But the lambdas in `_implement_loop` and `_test_loop` also call `process_task`, so `main` must import `process_task` as well. That still matches the roadmap line ("imports the flow from `pipeline`").
- `ParseResult` is imported in `main.py` today, and nothing uses it. It goes, and `pipeline` does not take it.
- After the move, `main` no longer uses `subprocess` or `NamedTuple`. It keeps using `time` (`run_implement`, `run_test`) and `sys` (`sys.exit` in the loops and `cli`).
- Nothing in the package imports `main` (`resume`, `runtime` and `state` do not), and nothing outside `tests/test_main.py` names the moved symbols on `main`.
- Reviewer duty (not an implementer task): on the review round that passes, and only then, the reviewer reads `../skills/.ai-factory/architects/trickster77777/07/address.md` at send time. It sends one `SendMessage` to the bare session name on that file's `session-name:` line, with the content the spec states in § What must be true after, records the tool's result verbatim above `REVIEW_PASS`, and keeps `REVIEW_PASS` as the last line. A failed or unavailable send is recorded, and the review still passes, with no `ESCALATION`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### The flow module

- [x] **Create `orchestrator/pipeline.py` with the flow**
  Files: `orchestrator/pipeline.py`
  Use the header shape of the sibling modules (`layout.py`, `protocol.py`). Start with a one-line module docstring, e.g. `"""The flow: the per-task pipeline, the mode record and its instances, and the roadmap loop."""`, then `from __future__ import annotations`. Then the stdlib imports: `import subprocess`, `import time`, `from pathlib import Path`, `from typing import NamedTuple`. Then the package imports, alphabetical by module:
  - `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, Implementer, PlannerReviewer, PlanReviewer`
  - `from .config import OrchestratorConfig`
  - `from .errors import EscalationError, HaltError, PipelineStopError`
  - `from .notify import Outcome, report`
  - `from .ports import VerifyKind`
  - `from .protocol import _read_sessions, _write_session`
  - `from .resume import _detect_step`
  - `from .roadmap import mark_done, mark_skipped, parse_roadmap`
  - `from .runtime import _run_summary`
  - `from .usage import _check_usage_limits`
  - `from . import state`

  Move these from `main.py` verbatim, in their current order, with bodies, docstrings, comments and printed/raised messages unchanged: `class Mode(NamedTuple)`, `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task`, `_run_dynamic_loop`. Do not carry `_run_loop` over.
  Every name the flow looks up (`PlannerReviewer`, `Implementer`, `PlanReviewer`, `mark_done`, `_git_commit`, `report`, `subprocess`, …) must stay a module-level lookup in `pipeline`, so the tests can patch them on `pipeline`. Nothing in `pipeline` imports `main` or `layout`.

### Rewire the composition root

- [x] **Strip the flow and `_run_loop` from `main.py` and import from `pipeline`** (depends on Create `orchestrator/pipeline.py`)
  Files: `orchestrator/main.py`
  - Delete `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `_run_loop`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task` and `_run_dynamic_loop`. Keep two blank lines between the remaining top-level definitions.
  - The remaining imports are exactly what `_test_loop`, `_implement_loop`, `run_implement`, `run_test`, `cli` and `if __name__ == "__main__"` use:
    - stdlib: `argparse`, `signal`, `sys`, `time`, `from pathlib import Path`. `subprocess` and `from typing import NamedTuple` go.
    - package: `from .config import OrchestratorConfig, load_config`; `from .errors import EscalationError, HaltError, PipelineStopError`; `from .layout import _artifact_subdir, _resolve_roadmap_relpath, _tests_sibling`; `from .notify import Outcome, report`; `from .pipeline import IMPLEMENT_MODE, TEST_MODE, _run_dynamic_loop, process_task` (alphabetical, after `.notify`); `from .runtime import _handle_sigint, _run_summary, _with_caffeinate`; `from . import state`.
    - Remove the `.agents`, `.ports`, `.protocol`, `.resume`, `.roadmap` and `.usage` imports.
  - `_test_loop`, `_implement_loop`, `run_implement`, `run_test`, `cli` and the `__main__` guard stay textually unchanged. `cli` must keep looking up `load_config`, `run_implement` and `report` in `main`'s own namespace, because `_run_cli_with` patches them there.
  - Update the module docstring `"""Orchestrator — Agent 1: loop through roadmap tasks."""` so it no longer claims the loop. Make it e.g. `"""Composition root and CLI: assemble the mode for a run and hand it to the flow."""`.
  - Leave `pyproject.toml` untouched: `orchestrator = "orchestrator.main:cli"` stays.

### Tests follow the owner

- [x] **Point the flow tests at `pipeline`** (depends on Strip the flow and `_run_loop` from `main.py`)
  Files: `tests/test_main.py`
  - Imports: add `from orchestrator import pipeline as pipeline_module` beside `from orchestrator import main as main_module`, keeping that alphabetical block (`errors`, `layout`, `main`, `pipeline`, `usage`). Replace the `from orchestrator.main import (IMPLEMENT_MODE, TEST_MODE, _artifact_dir, _next_number, process_task)` block with the same names imported `from orchestrator.pipeline import (...)`. Keep `main_module`, because the `cli` tests still use it.
  - `test_process_task_escalated_sidecar_raises_without_constructing_agents`: the five `monkeypatch.setattr(main_module, …)` calls for `"PlannerReviewer"`, `"Implementer"`, `"PlanReviewer"`, `"mark_done"` and `"_git_commit"` become `monkeypatch.setattr(pipeline_module, …)`.
  - The comment `# Production patterns verbatim from main.py` above `SESSION_PATTERN`/`WEEKLY_PATTERN` names the wrong home (the patterns live in `orchestrator/usage.py`). Make it `# Production patterns verbatim from usage.py`.
  - Leave everything else unchanged: `_run_cli_with`'s patches on `main_module.load_config`, `run_implement` and `report` stay valid, because `cli` stays in `main`. No test is added, removed or reworded.
  - Verify:
    - `grep -nE 'main_module, "(PlannerReviewer|Implementer|PlanReviewer|mark_done|_git_commit)"' tests/test_main.py` returns no matches. Name the file explicitly: grep given a bare directory without `-r` prints no matches and so proves nothing.
    - `grep -nE 'def (_run_loop|_next_number|_artifact_dir|_git_commit|process_task|_run_dynamic_loop)|class Mode|^(IMPLEMENT|TEST)_MODE|^import subprocess' orchestrator/main.py` returns no matches.
    - `grep -rn 'from \.main\|import main' orchestrator/` returns no matches.
    - `uv run pytest` passes with 227 tests, the same count as before.
    - `uv run python -c "import orchestrator.main"` succeeds.
