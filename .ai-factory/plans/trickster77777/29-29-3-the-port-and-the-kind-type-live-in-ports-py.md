# Plan: 29.3 — the port and the kind type live in `ports.py`

## Context
Move `VerifierProtocol` and `VerifyKind` out of `agents.py` into a new vocabulary module `orchestrator/ports.py`. The move also drops the `resume` → `agents` edge: the two thin wrappers `_detect_task_step` and `_detect_test_task_step` leave `resume.py` and become test helpers. This is behaviour-neutral and adds no new test. Spec: `.ai-factory/specs/trickster77777/0070-the-port-and-the-kind-type-live-in-ports.md`. Governing spec: `.ai-factory/ARCHITECTURE.md` § Dependency Rules (the vocabulary imports nothing from the package at runtime, and a type annotation counts as an edge) and § Folder Structure (`ports.py — Vocabulary: VerifierProtocol and the VerifyKind type`).

Assumption: the spec says "`agents` and `main` import `VerifierProtocol` and `VerifyKind` from `ports`". This plan reads that as "each imports from `ports` the names it uses". `main.py` names only `VerifyKind` (in the `Mode` record). It never names `VerifierProtocol`, because `process_task` calls `mode.verify.make_verifier(...)` without annotating the result. So `main` imports just `VerifyKind`, and no unused import is added.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Vocabulary module

- [x] **Create `orchestrator/ports.py` with the port and the kind type**
  Files: `orchestrator/ports.py`
  Follow the header shape of the sibling vocabulary modules `errors.py` and `protocol.py`: a one-line module docstring (e.g. `"""The verify port and the verify-kind type: what a verify step does, and everything that depends on which one runs."""`), then `from __future__ import annotations`, then stdlib imports only: `from pathlib import Path`, `from typing import Callable, NamedTuple, Protocol`. Move these from `agents.py` with docstrings, fields, field order and trailing comments unchanged:
  - `class VerifierProtocol(Protocol)` with `def verify(self, plan_path: Path, out_path: Path, prev_out_path: Path | None) -> bool: ...`
  - `class VerifyKind(NamedTuple)` with the fields `step`, `fail_tag`, `output_dirname`, `output_suffix`, `pass_signal`, `running_header`, `pass_line_label`, `fail_line_label`, `max_iterations_message`, `make_verifier`.
  The one change is the annotation of the last field: `make_verifier: Callable[[VerifierProtocol, Path], VerifierProtocol]  # (reviewer, project_dir) -> verifier`. The reviewer parameter is now typed by the port, so `ports` names no role. `ports.py` imports nothing from the `orchestrator` package, not even under `TYPE_CHECKING`.

### Rewire the importers

- [x] **`agents.py` takes the port and the type from `ports`** (depends on Create `orchestrator/ports.py`)
  Files: `orchestrator/agents.py`
  - Delete the `VerifierProtocol` and `VerifyKind` class definitions (they sit just above `_review_verifier`).
  - Add `from .ports import VerifierProtocol, VerifyKind` next to the existing `from .errors …` / `from .protocol …` imports, in alphabetical order (`.errors`, `.ports`, `.protocol`).
  - Change `from typing import Callable, NamedTuple, Protocol` to drop the names the module no longer uses. After the move nothing in `agents.py` uses `Callable`, `NamedTuple` or `Protocol` (verify with grep), so remove the whole `typing` import line.
  - Keep `_review_verifier`, `_test_run_verifier`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` in `agents.py` with bodies and instance values unchanged. Retype only the first parameter of both factories, from `PlannerReviewer` to `VerifierProtocol`: `def _review_verifier(planner_reviewer: VerifierProtocol, project_dir: Path) -> VerifierProtocol:` and `def _test_run_verifier(planner_reviewer: VerifierProtocol, project_dir: Path) -> VerifierProtocol:`. Keep the parameter names so the code stays byte-identical apart from the annotation.
  - `agents` re-exports nothing: do not alias or re-export `VerifierProtocol`/`VerifyKind` for other modules. `PlannerReviewer.verify` and `TestRunner.verify` keep reading `REVIEW_VERIFY.pass_signal` / `TEST_RUN_VERIFY.pass_signal` as they do today.

- [x] **`main.py` takes `VerifyKind` from `ports`** (depends on Create `orchestrator/ports.py`)
  Files: `orchestrator/main.py`
  Change `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, Implementer, PlannerReviewer, PlanReviewer, VerifyKind` to `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, Implementer, PlannerReviewer, PlanReviewer`. Add `from .ports import VerifyKind`, placed alphabetically among the relative imports (after `.notify`, before `.protocol`). No other change: `Mode.verify: VerifyKind`, `IMPLEMENT_MODE`/`TEST_MODE`, and `mode.verify.make_verifier(planner_reviewer, project_dir)` in `process_task` stay as they are. Passing a `PlannerReviewer` where `VerifierProtocol` is expected is structurally valid, since `PlannerReviewer.verify` matches the port's signature.

- [x] **`resume.py` drops the wrappers and the `agents` edge** (depends on Create `orchestrator/ports.py`)
  Files: `orchestrator/resume.py`
  - Replace `from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, VerifyKind` with `from .ports import VerifyKind`. Keep `from .protocol import _read_sessions`. After this, the only package imports in `resume` are `ports` and `protocol`.
  - Delete the two functions `_detect_task_step` and `_detect_test_task_step` at the end of the file. Leave nothing importable under those names in `resume`; per the spec's "What breaks on contact", a leftover wrapper would keep `resume` → `agents` alive.
  - Leave `_validate_sidecar_step`, `_plan_is_stale` and `_detect_step` byte-identical. That includes `_detect_step(..., verify: VerifyKind)` and its `endswith` checks, which belong to Phase 26 and not this task.

### Tests follow the move

- [x] **Wrappers become helpers in `tests/test_main.py`** (depends on `resume.py` drops the wrappers)
  Files: `tests/test_main.py`
  - In the `from orchestrator.resume import (...)` block, replace `_detect_task_step` and `_detect_test_task_step` with `_detect_step`, keeping `_validate_sidecar_step`. Add `from orchestrator.agents import REVIEW_VERIFY, TEST_RUN_VERIFY` among the existing `from orchestrator…` imports.
  - Define the two helpers locally, with the same names, signatures and bodies they had in `resume.py`. Put them in the `# _detect_task_step tests` section header area, before `_dms_dirs` (or just after the imports), so both the `test_detect_task_step_*` and `test_detect_test_task_step_*` tests can see them:
    ```python
    def _detect_task_step(
        project_dir: Path, seq: str, slug: str,
        plan_path: Path, plan_reviews_dir: Path, reviews_dir: Path,
    ) -> tuple[str, int, Path]:
        """Detect where a previous implement run stopped: `_detect_step` with `REVIEW_VERIFY`."""
        return _detect_step(
            project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir,
            REVIEW_VERIFY,
        )


    def _detect_test_task_step(
        project_dir: Path, seq: str, slug: str,
        plan_path: Path, plan_reviews_dir: Path, test_runs_dir: Path,
    ) -> tuple[str, int, Path]:
        """Detect where a previous test run stopped: `_detect_step` with `TEST_RUN_VERIFY`."""
        return _detect_step(
            project_dir, seq, slug, plan_path, plan_reviews_dir, test_runs_dir,
            TEST_RUN_VERIFY,
        )
    ```
  - Leave every `test_detect_task_step_*` and `test_detect_test_task_step_*` test body untouched; they now call the local helpers. Add no new test. The module docstring on line 1 still names both helpers and stays accurate, so leave it.
  - Check: `grep -rn "agents import.*VerifyKind\|agents import.*VerifierProtocol\|resume import.*_detect_task_step\|resume import.*_detect_test_task_step" orchestrator tests` returns nothing. `grep -n "^from \.\|^import" orchestrator/ports.py` shows no package import. `grep -n "from \.agents" orchestrator/resume.py` returns nothing. `uv run pytest` passes with the same test count as before the change.
