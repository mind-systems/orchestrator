# Plan: 29.1 — the outcome exceptions live in `errors.py`

## Context
Move the six outcome exceptions out of `orchestrator/agents.py` into a new vocabulary module `orchestrator/errors.py`. Every importer then takes them from `errors`, and the `usage` → `agents` edge disappears. This follows `.ai-factory/ARCHITECTURE.md` § Dependency Rules: `errors.py` sits in the Vocabulary layer and imports nothing from the package. The task spec is `.ai-factory/specs/trickster77777/0068-the-outcome-exceptions-live-in-errors.md`. The change is behaviour-neutral and adds no test.

Ground-truth note: the spec names one test reading `getattr(agents_module, "HaltError", None)`, `test_check_usage_limits_raises_halt_error_over_threshold`. `tests/test_main.py` has a second read of the same kind in `test_process_task_resume_past_max_iterations_raises_halt_error`. With no re-export, both would get `None` and fail, so both switch to `errors`. `agents_module` is used for nothing else in `tests/test_main.py`, so its import goes.

## Settings
- Testing: no (existing suite must stay green: `uv run pytest`)
- Logging: none
- Docs: no

## Tasks

### Move the exceptions

- [x] **Create `orchestrator/errors.py`**
  Files: `orchestrator/errors.py`
  Add a module docstring naming its concern, which is the outcome exceptions. Add `from __future__ import annotations` to match the sibling modules. Then move these classes from `orchestrator/agents.py` exactly as they are, with bases, bodies and docstrings character-for-character and in the same order: `HaltError(Exception)`, `RateLimitError(HaltError)`, `NetworkError(HaltError)`, `MissingArtifactError(HaltError)`, `PipelineStopError(Exception)`, `EscalationError(Exception)`. The module imports nothing from the `orchestrator` package and needs no other imports.

- [x] **Remove the classes from `agents.py` and import them from `errors`** (depends on Create `orchestrator/errors.py`)
  Files: `orchestrator/agents.py`
  Delete the six class definitions, which sit between `_classify_result` and `_sorted_nvm_node_dirs`. Add `from .errors import EscalationError, MissingArtifactError, NetworkError, RateLimitError` next to `from . import state`. That list holds exactly the names `agents.py` raises, so grep the file for `HaltError` and `PipelineStopError` and add either name only if it is actually used. Do not import any name for re-export, and add no `__all__` entry or alias.

- [x] **Point `main.py` and `usage.py` at `errors`** (depends on Create `orchestrator/errors.py`)
  Files: `orchestrator/main.py`, `orchestrator/usage.py`
  - `main.py`: remove `EscalationError`, `HaltError` and `PipelineStopError` from the `from .agents import …` line. Add `from .errors import EscalationError, HaltError, PipelineStopError`. Keep the remaining `agents` names (`REVIEW_VERIFY`, `TEST_RUN_VERIFY`, `Implementer`, `PlannerReviewer`, `PlanReviewer`, `VerifyKind`, `_read_sessions`, `_write_session`) as they are.
  - `usage.py`: replace `from .agents import HaltError` with `from .errors import HaltError`. After this, `usage.py` has no import from `agents`.

### Update the tests

- [x] **Import the exceptions from `errors` in the tests** (depends on Remove the classes from `agents.py`…)
  Files: `tests/test_agents.py`, `tests/test_main.py`
  - `tests/test_agents.py`: take `EscalationError`, `HaltError`, `MissingArtifactError` and `RateLimitError` out of the `from orchestrator.agents import (…)` block. Add `from orchestrator.errors import EscalationError, HaltError, MissingArtifactError, RateLimitError`. Leave every other import in that block where it is.
  - `tests/test_main.py`: replace `from orchestrator.agents import EscalationError, HaltError, PipelineStopError, RateLimitError` with `from orchestrator.errors import EscalationError, HaltError, PipelineStopError, RateLimitError`. Replace `from orchestrator import agents as agents_module` with `from orchestrator import errors as errors_module`. In `test_check_usage_limits_raises_halt_error_over_threshold` and `test_process_task_resume_past_max_iterations_raises_halt_error`, change `getattr(agents_module, "HaltError", None)` to `getattr(errors_module, "HaltError", None)` and keep the assertion unchanged.

### Verify

- [x] **Confirm no stale references and a green suite** (depends on all above)
  Files: none
  - Check for leftover `agents` imports of the six names. `pytest` cannot catch these: `agents` still holds four of the names through its own import from `errors`, so a missed import keeps resolving. A line grep is also not enough, because `tests/test_agents.py` imports through a multi-line parenthesized block. Read the import statements with `ast` instead. Run this from the repo root; it must print nothing and exit 0:
    ```bash
    uv run python -c "
    import ast, pathlib, sys
    six = {'HaltError','RateLimitError','NetworkError','MissingArtifactError','PipelineStopError','EscalationError'}
    bad = []
    for p in [*pathlib.Path('orchestrator').glob('*.py'), *pathlib.Path('tests').glob('*.py')]:
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[-1] == 'agents':
                bad += [f'{p}:{n.lineno} {a.name}' for a in n.names if a.name in six]
            if isinstance(n, ast.Attribute) and n.attr in six and isinstance(n.value, ast.Name) and n.value.id in {'agents','agents_module'}:
                bad.append(f'{p}:{n.lineno} {n.value.id}.{n.attr}')
    print('\\n'.join(bad)); sys.exit(1 if bad else 0)
    "
    ```
  - Run `grep -n "^class " orchestrator/agents.py`. None of the six classes may appear.
  - Run `grep -n "agents" orchestrator/usage.py`. It must show no import.
  - Run `uv run pytest`. Every test must pass, with no new tests and no changed assertions.
